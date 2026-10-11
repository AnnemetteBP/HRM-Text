import hashlib
import json
from pathlib import Path

from scripts.prepare_dfm10_andersen import EXPECTED_SHA256, validate_row, row_key


def test_versioned_andersen_holdout_is_original_split():
    root = Path(__file__).resolve().parents[1]
    path = root / 'evaluation/data/andersen/pairs_chunked_val.jsonl'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == EXPECTED_SHA256['validation']
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 119
    assert len({row_key(row) for row in rows}) == 119
    for line, row in enumerate(rows, 1):
        validate_row(row, path=path, line_number=line)
