import anthropic
import json
import logging
import os
import time
from typing import Generator
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
}


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(anthropic.RateLimitError),
)
def complete(system: str, user: str, tools: list = None, max_tokens: int = 4096) -> str:
    client = _client()
    kwargs = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    if tools:
        kwargs["tools"] = tools

    response = client.messages.create(**kwargs)

    if response.stop_reason == "tool_use":
        return _handle_tool_use(client, response, kwargs)

    text = response.content[0].text if response.content else ""
    logger.info(json.dumps({"model": MODEL, "system_len": len(system), "user_len": len(user), "response_len": len(text)}))
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
    return follow_up.content[0].text if follow_up.content else ""


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(anthropic.RateLimitError),
)
def stream_text(system: str, user: str, max_tokens: int = 4096) -> Generator[str, None, None]:
    client = _client()
    with client.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            yield text
