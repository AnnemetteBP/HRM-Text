"""Stage DFM15 native-reasoning repairs from DFM14; never promote live data."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
import os
from pathlib import Path
import shutil

import numpy as np
from tokenizers import Tokenizer

from dfm12.io import file_hash, load, lock, write_json
from dfm12.build_training import FIELDS
from dfm14.repair_reasoning import inventory, arrays, build_sample
from dfm14.native_reasoning import repair_row, native_template

MODE = 'native_thinking_and_direct_v2'


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
    source = np.load(Path(entry['path'])/'tokens.npy', mmap_mode='r')
    backing = np.load(base/'tokens.npy', mmap_mode='r')
    for start in range(0, len(source), 2_000_000):
        end = min(start+2_000_000, len(source))
        if not np.array_equal(source[start:end], backing[entry['offset']+start:entry['offset']+end]):
            raise ValueError('Frozen sampled source differs: '+entry['name'])
    a = arrays(Path(entry['path'])); n = len(a['inst_start'])
    indices = {k:np.lib.format.open_memmap(stage/(k+'.npy'), mode='w+', dtype=np.uint64, shape=(n,)) for k in FIELDS}
    valid = np.lib.format.open_memmap(stage/'valid.npy', mode='w+', dtype=np.uint8, shape=(n,))
    counts = Counter(); offset = 0; changed = 0
    with (stage/'tokens.raw').open('wb') as raw, gzip.open(stage/'evidence.jsonl.gz','wt') as evidence, \
            gzip.open(stage/'quarantine.jsonl.gz','wt') as quarantine:
        for i in range(n):
            old = {}
            for field in ('inst','resp'):
                start, length = int(a[field+'_start'][i]), int(a[field+'_len'][i])
                old[field] = tokenizer.decode(source[start:start+length].tolist(), skip_special_tokens=False)
            try:
                fixed = repair_row(old['inst'], old['resp'], tokenizer, norwegian=entry['norwegian'],
                                   terminal=entry['name'].startswith('nemotron_terminal_corpus_native__'))
            except ValueError as exc:
                counts['quarantined'] += 1
                reason = str(exc); counts['reject:'+reason] += 1
                quarantine.write(json.dumps(dict(source_row=i,reason=reason,original=old),ensure_ascii=False)+'\n')
                for k in FIELDS: indices[k][i] = offset if k.endswith('_start') else 0
                valid[i] = 0
            else:
                counts[fixed['action']] += 1
                counts['thinking' if fixed['enable_thinking'] else 'direct'] += 1
                valid[i] = 2 if fixed['enable_thinking'] else 1
                for field in ('inst','resp'):
                    values=np.asarray(fixed[field],dtype=source.dtype)
                    indices[field+'_start'][i]=offset; indices[field+'_len'][i]=len(values)
                    values.tofile(raw); offset += len(values)
                if fixed['prompt'] != old['inst'] or fixed['response'] != old['resp']:
                    changed += 1
                    evidence.write(json.dumps(dict(source_row=i,original=old,
                        **{k:v for k,v in fixed.items() if k not in ('inst','resp')}),ensure_ascii=False)+'\n')
            if (i+1)%10000 == 0:
                write_json(stage/'progress.json',dict(rows=i+1,total=n,counts=dict(counts)))
    for v in [*indices.values(), valid]: v.flush()
    target=np.lib.format.open_memmap(stage/'tokens.npy',mode='w+',dtype=source.dtype,shape=(offset,))
    if offset:
        source_raw=np.memmap(stage/'tokens.raw',dtype=source.dtype,mode='r',shape=(offset,))
        for start in range(0,offset,2_000_000): target[start:start+2_000_000]=source_raw[start:start+2_000_000]
        del source_raw
    target.flush(); del target
    (stage/'tokens.raw').unlink()
    result=dict(**entry,rows=n,changed=changed,new_tokens=offset,counts=dict(counts),mode=MODE)
    write_json(stage/'metadata.json',dict(reasoning_repair=result))
    write_json(stage/'complete.json',result)
    os.rename(stage,output)
    return result


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--workers',type=int,default=16)
    p.add_argument('--root',type=Path,default=Path('data/dfm15/native-reasoning-v2'))
    p.add_argument('--base',type=Path,default=Path('data/sampled_dfm14'))
    p.add_argument('--sample',action='store_true')
    args=p.parse_args(); args.root.mkdir(parents=True,exist_ok=True); args.base=args.base.resolve()
    os.environ['TOKENIZERS_PARALLELISM']='false'
    with lock(args.root/'.lock'):
        tokenizer=load(args.base/'metadata.json')['tokenizer_info']['tokenizer_path']
        pins={str(Path(__file__).resolve()):file_hash(Path(__file__)),
              'dfm14/native_reasoning.py':file_hash('dfm14/native_reasoning.py'),
              'dfm14/repair_reasoning.py':file_hash('dfm14/repair_reasoning.py'),
              'data_io/chat_templates/gemma4_native_chat.jinja':file_hash('data_io/chat_templates/gemma4_native_chat.jinja'),
              str(Path(tokenizer).resolve()):file_hash(tokenizer)}
        receipt=args.root/'implementation.json'
        if receipt.exists() and load(receipt)!=pins:
            raise ValueError('Implementation/tokenizer changed; use a fresh staging root')
        write_json(receipt,pins)
        (args.root/'chat_template.jinja').write_text(native_template())
        data=inventory(args.root,args.base)
        data['mode']=MODE; write_json(args.root/'inventory.json',data)
        jobs=[(str(args.root),str(args.base),e,tokenizer) for e in data['parts']]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results=[]
            for result in pool.map(repair_part,jobs):
                results.append(result); print(result['name'],result['counts'],flush=True)
        counts=Counter()
        for result in results: counts.update(result['counts'])
        write_json(args.root/'repairs.json',dict(mode=MODE,parts=results,counts=dict(counts)))
        write_json(args.root/'source-replacements.json',dict(mode=MODE,base=str(args.base),
            replacements=[dict(original=e['path'],repaired=str((args.root/'tokenized'/e['name']).resolve())) for e in results],
            publication='local staged only; not uploaded'))
        if args.sample: build_sample(args.root,args.base,results,native=True,output_name='sampled_dfm15')


if __name__=='__main__': main()
