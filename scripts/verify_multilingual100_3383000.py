"""Verify the completed comparison without rewriting its raw harness receipt."""
import json
from pathlib import Path

from eval_scheduler.model import JobStatus, read_plan
from eval_scheduler.validate_suites import compare

root = Path('logs/scheduler/multilingual100-comparison-3383000')
report = json.loads((root / 'result.json').read_text())
legacy = read_plan(root / 'legacy/plan.tsv')
assert len(legacy) == 200 and all(j.status == JobStatus.DONE for j in legacy)
for mode in report['modes'].values():
    assert mode['error'] is None
    assert len(mode['scores']) == 100
    assert all(s.get('completed_samples') == s.get('total_samples') == 500
               for s in mode['scores'])
    mode['complete'] = True
report['validation_note'] = (
    'Legacy succeeded with 100 inference and 100 export rows. The running harness '
    'incorrectly required 100 physical rows. Raw result.json is preserved; '
    'future harness runs validate logical IDs instead.'
)
report['score_differences'] = [compare(a, b) for a, b in zip(
    report['modes']['legacy']['scores'], report['modes']['shared']['scores'])]
(root / 'verified-comparison.json').write_text(json.dumps(report, indent=2) + '\n')
print('Verified both campaigns: 100 tasks and 50,000 examples each.')
