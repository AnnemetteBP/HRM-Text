from __future__ import annotations

import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from evaluation.engines import OpenAIEngine


class OpenAIEngineTest(unittest.TestCase):
    def test_caps_each_output_to_exact_remaining_context(self) -> None:
        engine = OpenAIEngine(
            "model",
            "http://127.0.0.1/v1",
            context_window=4096,
        )
        with (
            patch.object(
                engine,
                "_prompt_token_count",
                side_effect=[100, 1456],
            ),
            patch.object(
                engine,
                "_generate_one",
                return_value="answer",
            ) as generate_one,
        ):
            outputs = engine.generate(
                ["short", "long"],
                batch_size=2,
                max_tokens=3072,
            )

        self.assertEqual(outputs, ["answer", "answer"])
        budgets = sorted(
            call.kwargs["max_tokens"] for call in generate_one.call_args_list
        )
        self.assertEqual(budgets, [2640, 3072])

    def test_retries_context_overflow_with_remaining_output_budget(self) -> None:
        error_body = json.dumps(
            {
                "error": {
                    "message": (
                        "This model's maximum context length is 4096 tokens. "
                        "However, you requested 3072 output tokens and your prompt "
                        "contains at least 1025 input tokens, for a total of at least "
                        "4097 tokens."
                    )
                }
            }
        ).encode()
        context_error = urllib.error.HTTPError(
            "http://127.0.0.1/v1/chat/completions",
            400,
            "Bad Request",
            {},
            io.BytesIO(error_body),
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "answer"}}]}
        ).encode()

        engine = OpenAIEngine("model", "http://127.0.0.1/v1")
        with patch(
            "evaluation.engines.urllib.request.urlopen",
            side_effect=[context_error, response],
        ) as urlopen:
            result = engine._generate_one(
                "prompt",
                max_tokens=3072,
                temperature=0.0,
                stop=None,
                stop_token_ids=None,
                skip_special_tokens=False,
            )

        self.assertEqual(result, "answer")
        self.assertEqual(urlopen.call_count, 2)
        retry_request = urlopen.call_args_list[1].args[0]
        retry_payload = json.loads(retry_request.data)
        self.assertEqual(retry_payload["max_tokens"], 3071)


if __name__ == "__main__":
    unittest.main()
