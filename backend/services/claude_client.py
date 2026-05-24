import anthropic
import json
import logging
import os
import time
from pathlib import Path
from typing import AsyncGenerator, Optional
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

LOG_DIR = Path.home() / "politikerapp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

api_logger = logging.getLogger("api_calls")
api_logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOG_DIR / "api_calls.jsonl")
handler.setFormatter(logging.Formatter("%(message)s"))
if not api_logger.handlers:
    api_logger.addHandler(handler)

MODEL = "claude-sonnet-4-20250514"


def _get_api_key() -> str:
    env_path = Path.home() / "politikerapp" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key:
                    return key
    return os.environ.get("ANTHROPIC_API_KEY", "")


def _log_call(system: str, user: str, response_preview: str, tools: list = None):
    api_logger.info(json.dumps({
        "timestamp": time.time(),
        "model": MODEL,
        "system_len": len(system),
        "user_len": len(user),
        "tools": [t.get("name") for t in (tools or [])],
        "response_preview": response_preview[:200],
    }))


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(anthropic.RateLimitError),
)
def complete(system: str, user: str, tools: list = None, max_tokens: int = 4096) -> str:
    client = anthropic.Anthropic(api_key=_get_api_key())
    kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if tools:
        kwargs["tools"] = tools

    response = client.messages.create(**kwargs)

    # Handle tool use responses (for web_search)
    if response.stop_reason == "tool_use":
        return _handle_tool_use(client, response, kwargs)

    text = response.content[0].text if response.content else ""
    _log_call(system, user, text, tools)
    return text


def _handle_tool_use(client: anthropic.Anthropic, response, original_kwargs: dict) -> str:
    messages = list(original_kwargs["messages"])
    messages.append({"role": "assistant", "content": response.content})

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps({"status": "searched", "query": block.input.get("query", "")}),
            })

    messages.append({"role": "user", "content": tool_results})

    follow_up = client.messages.create(
        model=original_kwargs["model"],
        max_tokens=original_kwargs["max_tokens"],
        system=original_kwargs["system"],
        messages=messages,
        tools=original_kwargs.get("tools", []),
    )

    text = follow_up.content[0].text if follow_up.content else ""
    _log_call(original_kwargs["system"], str(messages[-1]), text, original_kwargs.get("tools"))
    return text


def stream_text(system: str, user: str, max_tokens: int = 4096) -> AsyncGenerator[str, None]:
    """Returns a synchronous generator of text chunks for use with StreamingResponse."""

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(anthropic.RateLimitError),
    )
    def _inner():
        client = anthropic.Anthropic(api_key=_get_api_key())
        with client.messages.stream(
            model=MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    return _inner()


WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
}
