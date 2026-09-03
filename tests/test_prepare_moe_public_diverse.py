from scripts.prepare_moe_public_diverse import (
    SOURCES,
    raw_pairs,
    row_pairs,
    text_pair_from_messages,
)


def test_public_corpus_has_ten_distinct_families() -> None:
    assert [source.family for source in SOURCES] == [
        "danish",
        "math",
        "code_swe",
        "science",
        "general_instruction_chat",
        "explicit_reasoning",
        "long_form_instruction",
        "grounded_knowledge",
        "news",
        "creative_literary",
    ]
    by_family = {source.family: source for source in SOURCES}
    assert by_family["code_swe"].split == "agentless"
    assert by_family["science"].config == "rqa"
    assert by_family["explicit_reasoning"].config == "DeepSeek"


def test_message_rows_use_first_user_and_last_nonempty_assistant() -> None:
    row = {
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "draft"},
            {"role": "assistant", "content": "final"},
        ]
    }
    assert text_pair_from_messages(row) == ("question", "final")


def test_raw_pairs_create_multiple_bounded_continuations() -> None:
    pairs = list(raw_pairs("word " * 2_000, "Continue:"))
    assert len(pairs) >= 2
    assert all(prompt.startswith("Continue:\n\n") for prompt, _ in pairs)
    assert all(response for _, response in pairs)


def test_math_rows_accept_problem_and_solution() -> None:
    math = next(source for source in SOURCES if source.family == "math")
    assert list(row_pairs(math, {"problem": "1+1?", "solution": "2"})) == [
        ("1+1?", "2")
    ]
