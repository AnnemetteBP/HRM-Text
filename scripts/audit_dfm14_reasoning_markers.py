"""Read-only, deterministic source-stratified scan of rendered training tokens."""
import hashlib
import json
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer
import yaml

PATTERN = re.compile(r'</?think>|</?thinking>|\[/?THINK\]|\[/?THOUGHT\]|<\|im_start\|>|<\|im_end\|>', re.I)
TOKENIZER = None


def scan(item):
    name, entry = item
    rng = np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], 'little'))
    parts = entry['parts']
    selected = rng.choice(len(parts), min(5, len(parts)), replace=False)
    result = dict(source=name, hf=entry.get('hf'), parts=len(parts), sampled=0,
                  response_hits=0, prompt_hits=0, markers={}, examples=[])
    for pi in selected:
        part = Path(parts[int(pi)])
        a = {k: np.load(part/(k+'.npy'), mmap_mode='r') for k in
             ('inst_start', 'inst_len', 'resp_start', 'resp_len', 'tokens')}
        for i in rng.choice(len(a['inst_start']), min(20, len(a['inst_start'])), replace=False):
            result['sampled'] += 1
            for field in ('resp', 'inst'):
                start, length = int(a[field+'_start'][i]), int(a[field+'_len'][i])
                text = TOKENIZER.decode(a['tokens'][start:start+length].tolist(), skip_special_tokens=False)
                matches = list(PATTERN.finditer(text))
                if not matches:
                    continue
                result['response_hits' if field == 'resp' else 'prompt_hits'] += 1
                for m in matches:
                    result['markers'][m[0]] = result['markers'].get(m[0], 0)+1
                if len(result['examples']) < 4:
                    m = matches[0]
                    result['examples'].append(dict(part=str(part), row=int(i), field=field,
                        prefix=text[:240], excerpt=text[max(0,m.start()-100):m.end()+350]))
    return result


def main():
    global TOKENIZER
    TOKENIZER = Tokenizer.from_file('../brainsurgery/models/gemma4_31b/tokenizer.json')
    groups = defaultdict(lambda: dict(parts=[]))
    rules = yaml.safe_load(Path('data_io/prefix_config_dfm11.yaml').read_text())
    for p in sorted(Path('data/tokenized_dfm11').iterdir()):
        if not p.is_dir():
            continue
        rule = next((r for r in rules if p.name.startswith(r['prefix'])), {})
        if rule.get('repeat', 1) == 0 or rule.get('max_per_file') == 0:
            continue
        name = 'dfm11/'+rule.get('prefix', p.name.split('__')[0])
        groups[name]['parts'].append(str(p))
    for version in (12,13,14):
        path = (Path(f'data/dfm14/inheritance-reconciliation/sampled_dfm{version}/source-registry.json')
                if version != 14 else Path('config/dfm14_sources.json'))
        for e in json.loads(path.read_text())['additions']:
            if e.get('repeat',1) == 0:
                continue
            groups[f'dfm{version}/'+e['name']] = dict(parts=e.get('tokenized_parts',e.get('parts')), hf=e.get('hf_repo_id'))
    out=Path('logs/dfm14/reasoning-marker-audit'); out.mkdir(parents=True,exist_ok=True)
    destination = out/'source-sample.jsonl'
    previous = [json.loads(line) for line in destination.read_text().splitlines()] if destination.exists() else []
    previous = [r for r in previous if r['source'] in groups]
    destination.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in previous))
    done = {r['source'] for r in previous}
    pending = [(k,v) for k,v in groups.items() if k not in done]
    with destination.open('a') as handle, ThreadPoolExecutor(max_workers=32) as pool:
        for n,result in enumerate(pool.map(scan,pending),len(done)+1):
            handle.write(json.dumps(result,ensure_ascii=False)+'\n'); handle.flush()
            if result['response_hits'] or result['prompt_hits']:
                print(result['source'],result['response_hits'],result['prompt_hits'],result['sampled'],flush=True)
            if n%100 == 0: print('Scanned',n,'/',len(groups),flush=True)


if __name__ == '__main__':
    main()
