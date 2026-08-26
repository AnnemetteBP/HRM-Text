import threading
import urllib.error
import urllib.request
from typing import Any

import spaces
import torch
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_ID = "danish-foundation-models/DFM-Mimir"
MAX_CONTEXT_TOKENS = 4096
MAX_USER_CHARS = 12_000
MAX_HISTORY_MESSAGES = 24


tokenizer = None
model = None
MODEL_LOCK = threading.Lock()


def _validate_model_access(oauth_token: gr.OAuthToken | None) -> str:
    if oauth_token is None:
        raise gr.Error("Sign in with Hugging Face before chatting with Mimir.")
    request = urllib.request.Request(
        f"https://huggingface.co/{MODEL_ID}/resolve/main/config.json",
        headers={"Authorization": f"Bearer {oauth_token.token}"},
        method="HEAD",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise gr.Error("Hugging Face could not verify access to Mimir.")
    except urllib.error.HTTPError as error:
        if error.code in {401, 403}:
            raise gr.Error(
                "Your account does not yet have access to DFM Mimir. Open the model "
                "card, accept the research licence, then try again."
            ) from error
        raise gr.Error(f"Hugging Face access check failed with HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise gr.Error("Could not reach Hugging Face to verify model access.") from error
    return oauth_token.token


def _ensure_model(token: str) -> None:
    global model, tokenizer
    if model is not None and tokenizer is not None:
        return
    with MODEL_LOCK:
        if tokenizer is None:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=token, use_fast=True)
        if model is None:
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                token=token,
                dtype=torch.bfloat16,
                low_cpu_mem_usage=True,
            ).eval().to("cuda")


def _text_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"]
    return str(content)


def _conversation(
    message: str,
    history: list[dict[str, Any]] | None,
    system_prompt: str,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    for item in (history or [])[-MAX_HISTORY_MESSAGES:]:
        role = item.get("role")
        if role not in {"user", "assistant"}:
            continue
        messages.append({"role": role, "content": _text_content(item.get("content", ""))})

    messages.append({"role": "user", "content": message.strip()})
    return messages


def _render(messages: list[dict[str, str]]) -> dict[str, torch.Tensor]:
    return tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        enable_thinking=False,
        return_dict=True,
        return_tensors="pt",
    )


def _fit_context(
    messages: list[dict[str, str]],
    max_new_tokens: int,
) -> tuple[list[dict[str, str]], dict[str, torch.Tensor]]:
    prompt_budget = MAX_CONTEXT_TOKENS - max_new_tokens
    if prompt_budget < 256:
        raise gr.Error("The requested answer leaves too little room for the prompt.")

    fitted = list(messages)
    encoded = _render(fitted)
    while encoded["input_ids"].shape[-1] > prompt_budget:
        first_dialogue = 1 if fitted and fitted[0]["role"] == "system" else 0
        if len(fitted) - first_dialogue <= 1:
            raise gr.Error(
                "The current message is too long for Mimir's 4,096-token context window."
            )
        fitted.pop(first_dialogue)
        if first_dialogue < len(fitted) - 1 and fitted[first_dialogue]["role"] == "assistant":
            fitted.pop(first_dialogue)
        encoded = _render(fitted)
    return fitted, encoded


@spaces.GPU(duration=120)
def respond(
    message: str,
    history: list[dict[str, Any]] | None,
    system_prompt: str = "",
    max_new_tokens: int = 384,
    temperature: float = 0.2,
    top_p: float = 0.9,
    repetition_penalty: float = 1.05,
    oauth_token: gr.OAuthToken | None = None,
) -> str:
    """Chat with DFM Mimir in Danish or English using its native template."""
    message = message.strip()
    if not message:
        raise gr.Error("Write a message first.")
    if len(message) > MAX_USER_CHARS:
        raise gr.Error(f"Messages are limited to {MAX_USER_CHARS:,} characters.")

    token = _validate_model_access(oauth_token)
    _ensure_model(token)
    max_new_tokens = int(max_new_tokens)
    messages = _conversation(message, history, system_prompt)
    _, inputs = _fit_context(messages, max_new_tokens)
    inputs = {name: tensor.to(model.device) for name, tensor in inputs.items()}
    prompt_length = inputs["input_ids"].shape[-1]
    token_type_ids = torch.ones_like(inputs["input_ids"])

    do_sample = temperature > 0
    generation_args: dict[str, Any] = {
        **inputs,
        "token_type_ids": token_type_ids,
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "repetition_penalty": float(repetition_penalty),
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
        "use_cache": True,
    }
    if do_sample:
        generation_args.update(temperature=float(temperature), top_p=float(top_p))

    with torch.inference_mode():
        output_ids = model.generate(**generation_args)

    answer = tokenizer.decode(
        output_ids[0, prompt_length:],
        skip_special_tokens=True,
    ).strip()
    return answer or "Mimir returned an empty response. Try rephrasing the prompt."


CSS = """
:root {
  --mimir-ink: #1d2528;
  --mimir-red: #c83b36;
  --mimir-gold: #d9a928;
  --mimir-paper: #f7f7f4;
}
.gradio-container { max-width: 1120px !important; margin: 0 auto !important; }
.mimir-header {
  display: flex; align-items: center; gap: 18px; padding: 14px 4px 18px;
  border-bottom: 3px solid var(--mimir-red); margin-bottom: 14px;
}
.mimir-header img { width: 150px; height: auto; object-fit: contain; }
.mimir-header h1 { margin: 0; color: var(--mimir-ink); font-size: 1.75rem; letter-spacing: 0; }
.mimir-header p { margin: 4px 0 0; color: #526066; font-size: 0.95rem; }
.mimir-note {
  border-left: 4px solid var(--mimir-gold); background: var(--mimir-paper);
  padding: 9px 12px; margin: 0 0 12px; color: #394348; font-size: 0.88rem;
}
#mimir-chat { min-height: 460px; }
@media (max-width: 640px) {
  .mimir-header { align-items: flex-start; gap: 12px; }
  .mimir-header img { width: 100px; }
  .mimir-header h1 { font-size: 1.35rem; }
}
"""


with gr.Blocks(fill_height=True) as demo:
    gr.HTML(
        """
        <header class="mimir-header">
          <img src="/gradio_api/file=DFM-logo.png" alt="Danish Foundation Models">
          <div>
            <h1>DFM Mimir</h1>
            <p>A bilingual Danish-English research model built on HRM-Text.</p>
          </div>
        </header>
        <div class="mimir-note">
          Mimir is a research model and has not been specifically safety-aligned.
          Responses may be incorrect or biased. Do not submit sensitive information.
        </div>
        """
    )

    with gr.Row():
        gr.LoginButton("Sign in with Hugging Face")
        gr.Markdown(
            "[Accept the Mimir research licence](https://huggingface.co/"
            "danish-foundation-models/DFM-Mimir) before starting a chat."
        )

    system_prompt = gr.Textbox(
        label="System instruction",
        placeholder="Optional guidance for the conversation",
        lines=2,
        value="",
    )
    max_new_tokens = gr.Slider(
        64, 768, value=384, step=32, label="Maximum answer tokens"
    )
    temperature = gr.Slider(
        0.0, 1.2, value=0.2, step=0.05, label="Temperature"
    )
    top_p = gr.Slider(0.1, 1.0, value=0.9, step=0.05, label="Top-p")
    repetition_penalty = gr.Slider(
        1.0, 1.2, value=1.05, step=0.01, label="Repetition penalty"
    )

    chatbot = gr.Chatbot(
        elem_id="mimir-chat",
        height="58vh",
        layout="panel",
        buttons=["copy", "copy_all"],
        placeholder="Ask Mimir something in Danish or English.",
    )
    gr.ChatInterface(
        fn=respond,
        chatbot=chatbot,
        additional_inputs=[
            system_prompt,
            max_new_tokens,
            temperature,
            top_p,
            repetition_penalty,
        ],
        additional_inputs_accordion="Generation settings",
        examples=[
            ["Forklar forskellen mellem vejr og klima kort og præcist.", "", 384, 0.2, 0.9, 1.05],
            ["Skriv et lille Python-program, der tæller vokaler i en tekst.", "", 384, 0.2, 0.9, 1.05],
            ["Summarize the causes of the seasons in two sentences.", "", 384, 0.2, 0.9, 1.05],
            ["A class has 24 students and three eighths bike to school. Solve step by step.", "", 384, 0.2, 0.9, 1.05],
        ],
        cache_examples=False,
        flagging_mode="never",
        concurrency_limit=1,
        api_name="chat",
        api_description="Chat with DFM Mimir in Danish or English.",
        fill_height=True,
    )


if __name__ == "__main__":
    demo.launch(
        mcp_server=True,
        css=CSS,
        allowed_paths=["DFM-logo.png"],
        footer_links=[
            {"text": "Model card", "url": f"https://huggingface.co/{MODEL_ID}"},
            {"text": "Technical report", "url": "https://arxiv.org/abs/2608.13517"},
        ],
    )
