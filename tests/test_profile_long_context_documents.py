from __future__ import annotations

import pytest

from scripts.profile_long_context_documents import (
    BIN_LABELS,
    bin_label,
    profile_documents,
    require_release_eligible,
    row_passes_filters,
    select_hash_indices,
)


def source(status: str = "green") -> dict[str, str]:
    return {
        "source_id": "example",
        "source_url": "https://example.invalid/source",
        "publisher": "Example publisher",
        "native_status": "native",
        "licence": "CC0-1.0",
        "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "commercial_release_status": status,
    }


def test_token_bins_have_exact_boundaries() -> None:
    assert [bin_label(value) for value in (0, 4095, 4096, 8191, 8192, 16383, 16384, 32767, 32768, 59999, 60000)] == [
        "under_4k",
        "under_4k",
        "4k_8k",
        "4k_8k",
        "8k_16k",
        "8k_16k",
        "16k_32k",
        "16k_32k",
        "32k_60k",
        "32k_60k",
        "60k_plus",
    ]


def test_candidate_export_requires_green_human_decision() -> None:
    with pytest.raises(PermissionError, match="human-reviewed 'green'"):
        require_release_eligible(source("review"))


def test_profiles_and_emits_provenance_first_candidates() -> None:
    rows = [
        {"id": "short", "text": "kort", "title": "Kort"},
        {"id": "medium", "text": "a b c d e f", "title": "Mellem"},
        {"id": "long", "text": " ".join(["ord"] * 20), "title": "Lang"},
    ]
    summary, candidates, metadata = profile_documents(
        rows,
        source=source(),
        text_field="text",
        id_field="id",
        metadata_fields=["title"],
        language="da",
        count_tokens=lambda text: len(text.split()),
        min_chars=5,
        max_docs=None,
        emit_candidates=True,
        candidate_min_tokens=6,
        max_candidates_per_bin=10,
    )

    assert summary["stats"]["documents_seen"] == 3
    assert summary["stats"]["documents_profiled"] == 2
    assert summary["candidate_count"] == 2
    assert {row["source"]["document_id"] for row in candidates} == {"medium", "long"}
    assert all(row["stage"] == "source_document_not_instruction_data" for row in candidates)
    assert all(row["source"]["document_sha256"] for row in candidates)
    assert set(summary["bin_semantics"]) == set(BIN_LABELS)
    assert len(metadata) == 2
    assert all(not row["contains_source_text"] for row in metadata)
    assert all("text" not in row for row in metadata)


def test_profile_only_is_allowed_while_rights_are_under_review() -> None:
    summary, candidates, metadata = profile_documents(
        [{"id": "one", "text": "one two three"}],
        source=source("review"),
        text_field="text",
        id_field="id",
        metadata_fields=[],
        language="da",
        count_tokens=lambda text: len(text.split()),
        min_chars=1,
        max_docs=None,
        emit_candidates=False,
        candidate_min_tokens=1,
        max_candidates_per_bin=1,
    )
    assert summary["stats"]["documents_profiled"] == 1
    assert candidates == []
    assert len(metadata) == 1


def test_year_and_ocr_filters() -> None:
    assert row_passes_filters(
        {"date": "2004/05", "ocr": "Nej"},
        year_field="date",
        year_min=2004,
        year_max=None,
        ocr_field="ocr",
        ocr_value="Nej",
    )
    assert not row_passes_filters(
        {"date": "1904/05", "ocr": "Ja"},
        year_field="date",
        year_min=2004,
        year_max=None,
        ocr_field="ocr",
        ocr_value="Nej",
    )


def test_hash_sample_is_collection_wide_and_deterministic() -> None:
    rows = [
        {"id": str(index), "date": "2020", "ocr": "Nej"}
        for index in range(100)
    ]
    kwargs = dict(
        source_id="source",
        id_field="id",
        limit=10,
        seed=42,
        year_field="date",
        year_min=2004,
        year_max=None,
        ocr_field="ocr",
        ocr_value="Nej",
    )
    selected, eligible = select_hash_indices(rows, **kwargs)
    repeated, _ = select_hash_indices(rows, **kwargs)
    assert len(selected) == 10
    assert eligible == 100
    assert selected == repeated
    assert max(selected) >= 50
