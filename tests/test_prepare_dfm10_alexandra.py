from scripts.prepare_dfm10_alexandra import contiguous_mentions, extract_bio_entities


def test_extract_bio_entities_preserves_surface_order() -> None:
    assert extract_bio_entities(
        ["Kjeld", "Christensen", "fra", "SID"],
        ["B-PER", "I-PER", "O", "B-ORG"],
    ) == {
        "PER": ["Kjeld Christensen"],
        "ORG": ["SID"],
        "LOC": [],
        "MISC": [],
    }


def test_contiguous_mentions_splits_disjoint_cluster_positions() -> None:
    tokens = ["Kjeld", "Christensen", "sagde", "at", "han", "kom"]
    assert contiguous_mentions(tokens, [0, 1, 4]) == ["Kjeld Christensen", "han"]
