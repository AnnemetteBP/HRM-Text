from collections import Counter

import pytest

from scripts.prepare_dfm10_deepdive import convert_row


SYSTEM = """# Tools
<tools>
{"name":"search","description":"Search","input_schema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}
{"name":"click","description":"Click","input_schema":{"type":"object","properties":{"link_ids":{"type":"array","items":{"type":"integer"}}},"required":["link_ids"]}}
{"name":"open","description":"Open","input_schema":{"type":"object","properties":{"urls":{"type":"array","items":{"type":"string"}}},"required":["urls"]}}
{"name":"finish","description":"Finish","input_schema":{"type":"object","properties":{"answer":{"type":"string"}}}}
</tools>
"""


def source_row() -> dict:
    return {
        "id": 858,
        "question": "Which answer is supported?",
        "answer": "The supported answer.",
        "conversations": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Which answer is supported?"},
            {
                "role": "assistant",
                "content": (
                    "<think>private search reasoning</think>\nVisible filler\n"
                    '<tool_call>{"name":"search","arguments":{"query":"evidence"}}</tool_call>'
                ),
            },
            {"role": "tool", "content": "A search result"},
            {
                "role": "assistant",
                "content": (
                    "<think>private final reasoning</think>"
                    '<tool_call>{"name":"finish","arguments":{"answer":"verbose"}}</tool_call>'
                ),
            },
        ],
    }


def test_converts_native_tools_and_gold_final_answer() -> None:
    stats: Counter[str] = Counter()
    row = convert_row(source_row(), 7, stats)

    assert [tool["function"]["name"] for tool in row["tools"]] == [
        "search",
        "click",
        "open",
    ]
    call = row["messages"][1]
    response = row["messages"][2]
    assert call["content"] == ""
    assert call["tool_calls"][0]["function"] == {
        "name": "search",
        "arguments": {"query": "evidence"},
    }
    assert response["tool_call_id"] == call["tool_calls"][0]["id"]
    assert response["name"] == "search"
    assert row["messages"][-1] == {
        "role": "assistant",
        "content": "The supported answer.",
    }
    assert "<think>" not in str(row)
    assert "<tool_call>" not in str(row)
    assert stats["tool_calls"] == stats["tool_responses"] == 1
    assert stats["final_answers"] == 1


def test_rejects_unanswered_tool_call() -> None:
    row = source_row()
    del row["conversations"][3]
    with pytest.raises(ValueError, match="misplaced assistant"):
        convert_row(row, 0, Counter())
