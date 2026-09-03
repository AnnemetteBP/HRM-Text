from scripts.create_long_context_review_sheet import choose_rows, flatten_review_row


def row(index: int, label: str) -> dict:
    return {
        "source_id": "source",
        "document_id": str(index),
        "document_sha256": f"hash-{index}",
        "measurements": {"source_tokens": index * 1000, "length_bin": label},
        "metadata": {"titel": f"Title {index}", "skabt": "2020", "dannet ved OCR": "Nej"},
    }


def test_stratified_selection_is_deterministic_and_capped() -> None:
    rows = [row(index, label) for label in ("8k_16k", "16k_32k") for index in range(10)]
    selected = choose_rows(rows, ["8k_16k", "16k_32k"], per_bin=3, seed=42)
    repeated = choose_rows(rows, ["8k_16k", "16k_32k"], per_bin=3, seed=42)
    assert [item["document_id"] for item in selected] == [item["document_id"] for item in repeated]
    assert sum(item["measurements"]["length_bin"] == "8k_16k" for item in selected) == 3
    assert sum(item["measurements"]["length_bin"] == "16k_32k" for item in selected) == 3


def test_review_row_contains_empty_human_fields_and_no_text() -> None:
    flattened = flatten_review_row(row(9, "8k_16k"))
    assert flattened["title"] == "Title 9"
    assert flattened["danish_readability_1_5"] == ""
    assert flattened["decision"] == ""
    assert "text" not in flattened
