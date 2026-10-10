"""Join isolated benchmark receipts without altering original measurements."""
import json
import argparse
from pathlib import Path

from eval_scheduler.model import read_plan
from eval_scheduler.validate_suites import compare

root = Path('logs/scheduler')
old = root/'multilingual100-comparison-3383000'
parser = argparse.ArgumentParser()
parser.add_argument('--directory', type=Path, default=root/'multilingual100-direct-3386000')
parser.add_argument('--label', default='direct')
args = parser.parse_args()
new = args.directory
before = json.loads((old/'verified-comparison.json').read_text())
after = json.loads((new/'result.json').read_text())
assert [j.to_row() for j in read_plan(old/'sources.tsv')] == [
    j.to_row() for j in read_plan(new/'sources.tsv')]
modes = dict(before['modes'])
paths = {mode: old/mode for mode in modes}
if args.label != 'direct':
    previous = root/'multilingual100-direct-3386000'
    modes['direct32'] = json.loads((previous/'result.json').read_text())['modes']['direct']
    paths['direct32'] = previous/'direct'
modes[args.label] = after['modes']['direct']
paths[args.label] = new/'direct'
assert all(m['complete'] for m in modes.values())
differences = {name: [compare(a, b) for a, b in zip(modes['legacy']['scores'], m['scores'])]
               for name, m in modes.items() if name != 'legacy'}
report = dict(modes=modes, differences_from_legacy=differences,
    note='Sequential cold-server runs, shared filesystem/compiler caches; no W&B. '
         'Legacy completion validated separately because the first harness counted physical rows.')
timings = {}
for mode, path in paths.items():
    rows = [json.loads(line) for line in (path/'telemetry.jsonl').read_text().splitlines()]
    counts = {}; milestones = []
    for row in rows:
        for server in row.get('servers', {}).values():
            counts[server['pid']] = max(counts.get(server['pid'], 0),
                server.get('values', {}).get('vllm:request_success_total', 0))
        milestones.append((row['time']-rows[0]['time'], sum(counts.values())))
    first = next(t for t, n in milestones if n > 0)
    last = next(t for t, n in milestones if n >= 50000)
    timings[mode] = dict(first_completion_seconds=first, all_completions_seconds=last,
        completion_window_seconds=last-first,
        remaining_tail_seconds=modes[mode]['wall_seconds']-last)
report['sampled_timings'] = timings
(new/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
for name, m in modes.items():
    windows = m['measurements']['windows']
    util = windows['whole_campaign']['gpu_mean_utilization'].values()
    print(name, f"{m['wall_seconds']:.2f}s", f"whole GPU mean {sum(util)/len(util):.2f}%",
          f"KV peak {windows['whole_campaign']['max_kv_percent']:.2f}%")
    print('  sampled timings', timings[name])
for name, values in differences.items():
    primary = [abs(v['shared']-v['legacy']) for d in values for k, v in d.items()
               if k.endswith(('/macro_f1', '/mean'))]
    print(name, 'different task dictionaries', sum(bool(d) for d in values),
          'largest primary metric difference', max(primary, default=0))
