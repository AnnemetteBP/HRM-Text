from jinja2 import Environment

from moe_tokenizer_contract import (
    TOKENIZER_NAME,
    TOKENIZER_REVISION,
    TOKENIZER_VOCAB_SIZE,
    load_chat_template,
)
from scripts.prepare_moe_real_pilot import encode_pair


def test_open_euro_tokenizer_is_exactly_pinned() -> None:
    assert TOKENIZER_NAME == "openeurollm/tokenizer-128k-v2"
    assert TOKENIZER_REVISION == "5c1fc6c70779ec84580c2a68d75c6b569b3381f5"
    assert TOKENIZER_VOCAB_SIZE == 131_072


def test_chatml_training_render_extends_generation_prefix_exactly() -> None:
    template = Environment().from_string(load_chat_template())
    user = [{"role": "user", "content": "Hej"}]
    conversation = user + [{"role": "assistant", "content": "Goddag"}]
    common = {"bos_token": "<bos>", "eos_token": "<eos>"}

    prompt = template.render(
        messages=user,
        add_generation_prompt=True,
        **common,
    )
    full = template.render(
        messages=conversation,
        add_generation_prompt=False,
        **common,
    )

    assert prompt == "<bos><|im_start|>user\nHej<|im_end|>\n<|im_start|>assistant\n"
    assert full.startswith(prompt)
    assert full == prompt + "Goddag<|im_end|>\n<eos>"


def test_pilot_requests_plain_token_ids_from_transformers() -> None:
    class FakeTokenizer:
        def apply_chat_template(
            self,
            messages,
            *,
            tokenize,
            add_generation_prompt,
            return_dict,
        ):
            assert tokenize is True
            assert return_dict is False
            return [1, 2] if add_generation_prompt else [1, 2, 3, 4]

    encoded = encode_pair(FakeTokenizer(), "danish", "Hej", "Goddag", 8)

    assert encoded is not None
    assert encoded.instruction == [1, 2]
    assert encoded.response == [3, 4]
