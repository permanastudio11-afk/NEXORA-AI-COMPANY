
"""NEXORA V2 - AI model connection layer.

OpenAI-compatible API client with configurable provider,
secure secret loading, timeout and bounded error handling.
"""

import json
import os
import urllib.error
import urllib.request
import socket
from typing import Optional


class LLMError(Exception):
    """Raised when an AI provider request fails."""


def _get_setting(name: str, default: str = "") -> str:
    """Read configuration from environment or Streamlit Secrets."""
    value = os.getenv(name)

    if value:
        return value

    try:
        import streamlit as st
        value = st.secrets.get(name, default)
        return str(value) if value else default
    except Exception:
        return default


def get_config() -> dict:
    """Return the active AI provider configuration."""
    return {
        "api_key": _get_setting("OPENAI_API_KEY"),
        "base_url": _get_setting(
            "OPENAI_BASE_URL",
            "https://api.openai.com/v1"
        ).rstrip("/"),
        "model": _get_setting("OPENAI_MODEL", "gpt-4o-mini"),
        "timeout": int(_get_setting("LLM_TIMEOUT", "60")),
        "max_tokens": int(_get_setting("LLM_MAX_TOKENS", "2000")),
    }


def is_configured() -> bool:
    """Check whether an API key is available."""
    return bool(get_config()["api_key"])


def chat(
    messages: list,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:
    """Send messages to an OpenAI-compatible chat completion API.

    messages example:
        [{"role": "user", "content": "Hello"}]
    """
    config = get_config()

    if not config["api_key"]:
        raise LLMError(
            "API key belum dikonfigurasi. "
            "Tambahkan OPENAI_API_KEY melalui Streamlit Secrets."
        )

    if not messages:
        raise LLMError("Pesan tidak boleh kosong.")

    if not 0 <= temperature <= 2:
        raise LLMError("Temperature harus antara 0 dan 2.")

    payload_messages = []

    if system_prompt:
        payload_messages.append({
            "role": "system",
            "content": system_prompt
        })

    for message in messages:
        if not isinstance(message, dict):
            raise LLMError("Format pesan tidak valid.")

        role = message.get("role")
        content = message.get("content")

        if role not in ("system", "user", "assistant"):
            raise LLMError(f"Role pesan tidak didukung: {role}")

        if not isinstance(content, str) or not content.strip():
            raise LLMError("Isi pesan harus berupa teks.")

        payload_messages.append({
            "role": role,
            "content": content
        })

    token_limit = max_tokens or config["max_tokens"]

    if token_limit < 1 or token_limit > 16000:
        raise LLMError("Batas token harus antara 1 dan 16000.")

    payload = {
        "model": config["model"],
        "messages": payload_messages,
        "temperature": temperature,
        "max_tokens": token_limit,
    }

    url = config["base_url"] + "/chat/completions"

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=config["timeout"]
        ) as response:
            result = json.loads(response.read().decode("utf-8"))

        choices = result.get("choices", [])

        if not choices:
            raise LLMError("Provider tidak mengembalikan hasil.")

        content = choices[0].get("message", {}).get("content")

        if not isinstance(content, str) or not content.strip():
            raise LLMError("Jawaban AI kosong atau tidak valid.")

        return content.strip()

    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise LLMError(
            f"AI provider HTTP {exc.code}: {detail[:1000]}"
        ) from exc

    except urllib.error.URLError as exc:
        raise LLMError(
            f"Koneksi ke AI provider gagal: {exc.reason}"
        ) from exc

    except TimeoutError as exc:
        raise LLMError("Permintaan AI melewati batas waktu.") from exc

    except json.JSONDecodeError as exc:
        raise LLMError("Respons AI bukan JSON yang valid.") from exc
