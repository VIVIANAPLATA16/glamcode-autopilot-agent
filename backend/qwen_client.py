"""Shared Qwen Cloud API client (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"


def _get_client() -> OpenAI:
    api_key = os.getenv("QWEN_API_KEY")
    if not api_key:
        raise ValueError(
            "QWEN_API_KEY no está configurada. Copia .env.example a .env y agrega tu API key."
        )
    base_url = os.getenv("QWEN_API_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model() -> str:
    return os.getenv("QWEN_MODEL", DEFAULT_MODEL)


def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    response_format_json: bool = False,
) -> str:
    """Call Qwen chat completions and return assistant text content."""
    client = _get_client()
    model = _get_model()

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if response_format_json:
        kwargs["response_format"] = {"type": "json_object"}

    logger.debug("Qwen request model=%s messages=%d", model, len(messages))
    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content or ""
    logger.debug("Qwen response length=%d", len(content))
    return content.strip()


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract and parse JSON from model output, tolerating markdown fences."""
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from Qwen: %s", cleaned[:200])
        raise ValueError("La respuesta del modelo no es JSON válido.") from exc
