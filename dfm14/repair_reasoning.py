"""CPU-only legacy reasoning-wrapper repair, staged without touching live data.

The current DFM14 contract is non-thinking: keep reasoning as ordinary answer
text, not hidden channels. Preserve every sampled row, its order and repeat.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
import os
from pathlib import Path
import re
import shutil

import numpy as np
from tokenizers import Tokenizer

from dfm12.io import file_hash, load, lock, write_json
from dfm12.build_training import FIELDS
from dfm14.reconcile_inheritance import validate

ROOT = Path('data/dfm14/reasoning-repair-v1')
BASE = Path('data/sampled_dfm14')
PREFIXES = ('allenai_big_reasoning_traces__', 'allenai_open_math_2_50k_r1__',
            'allenai_verifiable_reasoning_gpt41__', 'allenai_verifiable_reasoning_o4mini__',
            'nemotron_terminal_corpus_native__')
NORWEGIAN = 'dfm12-norwegian-magpie-qwen3-bokmaal'
LEGACY = re.compile(r'</?think>', re.I)
TURNS = re.compile(r'(<\|turn>(?:system|user|model|tool)\n)')


def clean_meta_references(body):
    """Modernize prose references to legacy reasoning tags, not code examples."""
    paragraphs=body.split('\n\n')
    for i,text in enumerate(paragraphs):
        if ('```' not in text and LEGACY.search(text)
                and re.search(r'\b(reasoning|traces?|outline|derivation|solution|steps?|thought|private|hidden|explanation|details|work|log|analysis|count|method|summary)\b',text,re.I)
                and not re.match(r'^\s*<think>',text,re.I)):
            text=re.sub(r'[`"\u201c\u201d\u2018\u2019]*<think>(?:\u2026|\.\.\.)</think>[`"\u201c\u201d\u2018\u2019]*','reasoning',text,flags=re.I)
            text=re.sub(r'[`"\u201c\u201d\u2018\u2019]*</?think>[`"\u201c\u201d\u2018\u2019]*','reasoning',text,flags=re.I)
            text=text.replace('in reasoning tags','as step-by-step reasoning')
            text=text.replace('in <answer> tags','as the final answer')
            text=re.sub(r'\breasoning(?:\s+reasoning)+\b','reasoning',text)
            paragraphs[i]=text
    return '\n\n'.join(paragraphs)


def clean_body(text, role, norwegian=False, depth=0):
    """Only consume structural wrappers; quoted/ambiguous markup fails closed."""
    ending = '<turn|>\n' if text.endswith('<turn|>\n') else ''
    body = text[:-len(ending)] if ending else text
    original = body
    if role == 'model':
        body=re.sub(r'(?m)^[ \t]*#{1,6}[ \t]+(?=</?(?:think|answer)>)','',body)
        body=clean_meta_references(body)
        # Some upstream traces contain thousands of duplicated closing tags.
        # An outer leading think block identifies these as serialized traces,
        # not a plain-text explanation of the tag syntax.
        if re.match(r'^\s*<think>',body,re.I):
            body = LEGACY.sub('\n\n',body)
            body = re.sub(r'</?answer>', '\n\n', body)
            body = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',body).strip()
            return body+ending
        opening = re.search(r'(?<![`"\u201c\u201d\u2018\u2019])<think>\s*', body, re.I)
        closing = re.compile(r'</think>',re.I).search(body,opening.end() if opening else 0)
        if opening:
            if closing:
                prefix = body[:opening.start()].strip()
                thought = body[opening.end():closing.start()].strip()
                answer = body[closing.end():].strip()
                body = '\n\n'.join(x for x in (prefix, thought, unwrap_answer(answer)) if x)
            else:
                body = body[:opening.start()]+body[opening.end():]
        elif closing:
            tail = body[closing.end():].strip()
            # Several AllenAI sources omitted the opening tag but retained
            # </think><answer> boundaries. Do not rewrite arbitrary quotations.
            before = body[:closing.start()]
            quoted = before.endswith(('`', '"', "'")) or tail.startswith(('`', '"', "'"))
            if not quoted:
                body = '\n\n'.join(x for x in
                    (before.strip(), unwrap_answer(tail)) if x)
        elif body.lstrip().startswith('<answer>'):
            body = unwrap_answer(body.strip())
    elif norwegian and role == 'user':
        body = re.sub(r'\s*</think>\s*$', '', body, flags=re.I)
    if role == 'model' and LEGACY.search(body):
        body=clean_meta_references(body)
    if LEGACY.search(body):
        if body != original and depth < 32:
            return clean_body(body+ending,role,norwegian,depth+1)
        raise ValueError('Ambiguous or embedded legacy reasoning markup: '+body[:150])
    return (body + ending) if body != original else text


def unwrap_answer(text):
    match = re.fullmatch(r'<answer>\s*(.*?)\s*</answer>', text, re.S)
    if match:
        return match[1]
    # A truncated target may not have its closing answer tag yet.
    return re.sub(r'^<answer>\s*', '', text)


def repair_rendered(text, *, response=False, norwegian=False):
    parts = TURNS.split(text)
    role = 'model' if response else 'system'
    result = [clean_body(parts[0], role, norwegian)]
    for header, body in zip(parts[1::2], parts[2::2]):
        role = header[len('<|turn>'):-1]
        result.extend((header, clean_body(body, role, norwegian)))
    return ''.join(result)


def arrays(path):
    return {k: np.load(path/(k+'.npy'), mmap_mode='r') for k in FIELDS}


def inventory(root, base):
    receipt = root/'inventory.json'
    if receipt.exists():
        result = load(receipt)
        if result['base'] != str(base.resolve()) or result['metadata_sha256'] != file_hash(base/'metadata.json'):
            raise ValueError('Frozen input changed')
        return result
    parts = []; offset = 0
    for path in sorted(Path('data/tokenized_dfm11').iterdir()):
        if not path.is_dir():
            continue
        tokens = np.load(path/'tokens.npy', mmap_mode='r')
        if path.name.startswith(PREFIXES):
            parts.append(dict(path=str(path.resolve()), name=path.name, offset=offset,
                              tokens=len(tokens), norwegian=False))
        offset += len(tokens)
    if offset != len(np.load('data/sampled_dfm11/tokens.npy', mmap_mode='r')):
        raise ValueError('DFM11 source offsets do not match frozen backing')
    for path in sorted(Path('data/dfm14/inheritance-reconciliation/dfm12_tokenized').iterdir()):
        if not path.is_dir():
            continue
        tokens = np.load(path/'tokens.npy', mmap_mode='r')
        if path.name.startswith(NORWEGIAN+'__'):
            parts.append(dict(path=str(path.resolve()), name=path.name, offset=offset,
                              tokens=len(tokens), norwegian=True))
        offset += len(tokens)
    if offset != len(np.load('data/sampled_dfm12/tokens.npy', mmap_mode='r')):
        raise ValueError('DFM12 source offsets do not match frozen backing')
    result = dict(base=str(base.resolve()), metadata_sha256=file_hash(base/'metadata.json'),
                  tokenizer_sha256=file_hash(load(base/'metadata.json')['tokenizer_info']['tokenizer_path']),
                  mode='nonthinking_preserve_reasoning_remove_legacy_wrappers', parts=parts)
    write_json(receipt, result)
    return result


def repair_part(job):
    root, base, entry, tokenizer_path = job
    root, base = Path(root), Path(base)
    output = root/'tokenized'/entry['name']
    if (output/'complete.json').exists():
        return load(output/'complete.json')
    stage = output.with_name(output.name+'.building')
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    tokenizer = Tokenizer.from_file(tokenizer_path)
    path = Path(entry['path']); source = np.load(path/'tokens.npy', mmap_mode='r')
    backing = np.load(base/'tokens.npy', mmap_mode='r')
    for start in range(0,len(source),2_000_000):
        end=min(start+2_000_000,len(source))
        if not np.array_equal(source[start:end],
            backing[entry['offset']+start:entry['offset']+end]):
            raise ValueError('Frozen sampled source differs: '+entry['name'])
    a = arrays(path); n = len(a['inst_start'])
    index = {k:np.lib.format.open_memmap(stage/(k+'.npy'),mode='w+',dtype=np.uint64,shape=(n,)) for k in FIELDS}
    changed = 0; offset = 0; failures = 0
    with (stage/'tokens.raw').open('wb') as raw, gzip.open(stage/'changed-rendered.jsonl.gz','wt') as evidence, \
            (stage/'unresolved.jsonl').open('w') as rejected:
        for i in range(n):
            texts = {}; altered = False
            for field in ('inst','resp'):
                start, length = int(a[field+'_start'][i]), int(a[field+'_len'][i])
                old = source[start:start+length]
                text = tokenizer.decode(old.tolist(),skip_special_tokens=False)
                try:
                    fixed = repair_rendered(text,response=field=='resp',norwegian=entry['norwegian'])
                except ValueError as exc:
                    rejected.write(json.dumps(dict(row=i,field=field,error=str(exc),text=text),ensure_ascii=False)+'\n')
                    failures += 1; fixed = text
                values = (np.asarray(tokenizer.encode(fixed,add_special_tokens=False).ids,dtype=source.dtype)
                          if fixed != text else old)
                index[field+'_start'][i] = offset; index[field+'_len'][i] = len(values)
                values.tofile(raw); offset += len(values)
                texts[field] = fixed; altered |= fixed != text
            if altered:
                changed += 1
                evidence.write(json.dumps(dict(source_row=i,prompt=texts['inst'],response=texts['resp']),ensure_ascii=False)+'\n')
            if (i+1)%10000 == 0:
                write_json(stage/'progress.json',dict(rows=i+1,total=n,changed=changed,unresolved=failures))
    for v in index.values(): v.flush()
    if failures:
        raise ValueError(f'{entry["name"]}: {failures} ambiguous fields; see {stage}/unresolved.jsonl')
    source_raw = np.memmap(stage/'tokens.raw',dtype=source.dtype,mode='r',shape=(offset,))
    target = np.lib.format.open_memmap(stage/'tokens.npy',mode='w+',dtype=source.dtype,shape=(offset,))
    for start in range(0,offset,2_000_000): target[start:start+2_000_000] = source_raw[start:start+2_000_000]
    target.flush(); del target,source_raw
    (stage/'tokens.raw').unlink()
    result = dict(**entry,rows=n,changed=changed,new_tokens=offset,unresolved=0)
    write_json(stage/'complete.json',result)
    write_json(stage/'metadata.json',dict(reasoning_repair=result))
    os.rename(stage,output)
    return result


def build_sample(root, base, entries, *, native=False, output_name='sampled_dfm14'):
    """Redirect affected rows only; preserve all epoch selections and ordering."""
    output = root/output_name
    if (output/'ready.json').exists(): return
    output.mkdir(exist_ok=True)
    old_tokens = np.load(base/'tokens.npy',mmap_mode='r')
    offsets=[]; total=len(old_tokens)
    for e in entries:
        offsets.append(total); total += e['new_tokens']
    if not (output/'token-copy.json').exists():
        dest=np.lib.format.open_memmap(output/'tokens.npy',mode='w+',dtype=old_tokens.dtype,shape=(total,))
        for source,offset in [(old_tokens,0)]+[(np.load(root/'tokenized'/e['name']/'tokens.npy',mmap_mode='r'),o) for e,o in zip(entries,offsets)]:
            for i in range(0,len(source),8_000_000):
                end=min(i+8_000_000,len(source))
                dest[offset+i:offset+end] = source[i:end]
                if i%1_000_000_000 == 0:
                    dest.flush(); print('Token copy',offset+i,'/',total,flush=True)
        dest.flush(); del dest
        write_json(output/'token-copy.json',dict(tokens=total,base_tokens=len(old_tokens)))
    maps=[]
    for e,o in zip(entries,offsets):
        before=arrays(Path(e['path'])); after=arrays(root/'tokenized'/e['name'])
        starts=before['inst_start']
        if np.any(starts[1:]<=starts[:-1]): raise ValueError('Nonunique source-row starts')
        valid = np.load(root/'tokenized'/e['name']/'valid.npy', mmap_mode='r') if native else None
        maps.append((e,o,before,after,valid))
    reports=[]
    for epoch in sorted(base.glob('epoch_*')):
        dest_dir=output/epoch.name; dest_dir.mkdir(exist_ok=True)
        if (dest_dir/'repair.json').exists():
            reports.append(load(dest_dir/'repair.json')); continue
        old=arrays(epoch); n=len(old['inst_len'])
        new={k:np.lib.format.open_memmap(dest_dir/(k+'.npy'),mode='w+',dtype=np.uint64,shape=(n,)) for k in FIELDS}
        changed=0; tokens=0; written=0; dropped=0; thinking=0
        for i in range(0,n,1_000_000):
            a={k:np.array(v[i:i+1_000_000],dtype=np.uint64) for k,v in old.items()}
            keep=np.ones(len(a['inst_start']),dtype=bool)
            for e,o,before,after,valid in maps:
                mask=(a['inst_start']>=e['offset']) & (a['inst_start']<e['offset']+e['tokens'])
                if not mask.any(): continue
                rows=np.searchsorted(before['inst_start'],a['inst_start'][mask]-e['offset'])
                if np.any(rows>=len(before['inst_start'])) or not np.array_equal(before['inst_start'][rows]+e['offset'],a['inst_start'][mask]):
                    raise ValueError('Sampled source row cannot be mapped')
                if not np.array_equal(before['resp_start'][rows]+e['offset'],a['resp_start'][mask]):
                    raise ValueError('Target pointer mismatch')
                for k in FIELDS:
                    a[k][mask]=after[k][rows]+(o if k.endswith('_start') else 0)
                if native:
                    keep[mask]=valid[rows]>0
                    thinking += int((valid[rows]==2).sum())
                    if np.any((a['inst_len'][mask]+a['resp_len'][mask])[valid[rows]>0]>4097):
                        raise ValueError('Native row would truncate thought/final boundary')
                else:
                    allowed=4097-np.minimum(a['inst_len'][mask],4097)
                    a['resp_len'][mask]=np.minimum(a['resp_len'][mask],allowed)
                    if np.any(a['resp_len'][mask]==0): raise ValueError('Repair would remove a training row')
                changed += int(mask.sum())
            dropped += int((~keep).sum())
            a={k:v[keep] for k,v in a.items()}
            for k in FIELDS: new[k][written:written+len(a[k])]=a[k]
            written += len(a['inst_start'])
            tokens += int(a['inst_len'].sum())+int(a['resp_len'].sum())
        for v in new.values():v.flush()
        if written != n:
            for k in FIELDS:
                compact=dest_dir/(k+'.compact.npy')
                dest=np.lib.format.open_memmap(compact,mode='w+',dtype=np.uint64,shape=(written,))
                for start in range(0,written,1_000_000):dest[start:start+1_000_000]=new[k][start:min(start+1_000_000,written)]
                dest.flush();del dest
                del new[k]
                os.replace(compact,dest_dir/(k+'.npy'))
        report=dict(epoch=epoch.name,rows=written,tokens=tokens,redirected_rows=changed,
                    quarantined_occurrences=dropped,native_thinking_occurrences=thinking)
        write_json(dest_dir/'repair.json',report); reports.append(report)
        print('Patched epoch',report,flush=True)
    metadata=load(base/'metadata.json'); metadata['total_length']=round(sum(r['tokens'] for r in reports)/len(reports))
    if native:
        metadata['tokenizer_info']=dict(metadata.get('tokenizer_info',{}),
            chat_template_path=str((root/'chat_template.jinja').resolve()))
        metadata['reasoning_policy']={'mode':'per_example_native_thinking_or_direct',
            'scope':'listed repaired sources; inherited rows unchanged',
            'receipt':str((root/'repairs.json').resolve())}
    write_json(output/'metadata.json',metadata)
    validate(output,len(reports))
    write_json(output/'ready.json',dict(status='validated_staged_not_promoted',base=str(base.resolve()),
        mode='native_thinking_and_direct' if native else 'nonthinking_preserve_reasoning_remove_legacy_wrappers',epochs=reports,
        note='Original backing retained but affected sampled rows redirected to repaired arrays.'))


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--workers',type=int,default=16)
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--base',type=Path,default=BASE)
    p.add_argument('--sample',action='store_true')
    args=p.parse_args(); args.root.mkdir(parents=True,exist_ok=True)
    args.base=args.base.resolve()
    os.environ['TOKENIZERS_PARALLELISM']='false'
    with lock(args.root/'.lock'):
        data=inventory(args.root,args.base)
        tokenizer=load(args.base/'metadata.json')['tokenizer_info']['tokenizer_path']
        jobs=[(str(args.root),str(args.base.resolve()),e,tokenizer) for e in data['parts']]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results=[]
            for result in pool.map(repair_part,jobs):
                results.append(result); print(result['name'],result['changed'],'/',result['rows'],flush=True)
        write_json(args.root/'repairs.json',dict(parts=results,changed_rows=sum(r['changed'] for r in results)))
        write_json(args.root/'source-replacements.json',dict(
            mode=data['mode'],inherits=str(args.base),
            replaces=[dict(original=e['path'],repaired=str((args.root/'tokenized'/e['name']).resolve()),
                           original_sampled_token_offset=e['offset']) for e in results],
            publication='local repair; not uploaded',
            status='repaired_sources_ready_for_staged_sampling'))
        if args.sample:build_sample(args.root,args.base.resolve(),results)


if __name__=='__main__':main()
