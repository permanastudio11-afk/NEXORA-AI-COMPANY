
"""NEXORA V2 - Resilient AI model connection layer."""

import json
import os
import random
import socket
import time
import urllib.error
import urllib.request
from typing import Optional


class LLMError(Exception):
    """Raised when an AI provider request fails."""


RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_RETRIES = 3


def _get_setting(name: str, default: str = "") -> str:
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
    try:
        timeout = int(_get_setting("LLM_TIMEOUT", "60"))
        max_tokens = int(_get_setting("LLM_MAX_TOKENS", "2000"))
    except ValueError as exc:
        raise LLMError("Konfigurasi timeout atau max_tokens tidak valid.") from exc

    if timeout < 1 or max_tokens < 1:
        raise LLMError("Timeout dan max_tokens harus lebih besar dari nol.")

    return {
        "api_key": _get_setting("OPENAI_API_KEY"),
        "base_url": _get_setting(
            "OPENAI_BASE_URL",
            "https://api.openai.com/v1"
        ).rstrip("/"),
        "model": _get_setting("OPENAI_MODEL", "gpt-4o-mini"),
        "timeout": timeout,
        "max_tokens": max_tokens,
    }


def is_configured() -> bool:
    config = get_config()
    return bool(
        config["api_key"]
        and config["base_url"]
        and config["model"]
    )


def _retry_delay(attempt: int, headers=None) -> float:
    """Calculate retry delay, respecting Retry-After when available."""

    if headers:
        retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return min(max(float(retry_after), 0), 30)
            except ValueError:
                pass

    return min(2 ** attempt + random.uniform(0, 0.5), 30)


def chat(
    messages: list,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:

    config = get_config()

    if not config["api_key"]:
        raise LLMError("API key belum dikonfigurasi.")

    if not config["base_url"] or not config["model"]:
        raise LLMError("Base URL atau model AI belum dikonfigurasi.")

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
            raise LLMError(f"Role tidak didukung: {role}")

        if not isinstance(content, str) or not content.strip():
            raise LLMError("Isi pesan harus berupa teks.")

        payload_messages.append({
            "role": role,
            "content": content
        })

    token_limit = (
        max_tokens if max_tokens is not None
        else config["max_tokens"]
    )

    if token_limit < 1 or token_limit > 16000:
        raise LLMError("Batas token harus antara 1 dan 16000.")

    payload = {
        "model": config["model"],
        "messages": payload_messages,
        "temperature": temperature,
        "max_tokens": token_limit,
    }

    url = config["base_url"] + "/chat/completions"

    body = json.dumps(payload).encode("utf-8")

    for attempt in range(MAX_RETRIES + 1):

        request = urllib.request.Request(
            url,
            data=body,
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
                result = json.loads(
                    response.read().decode("utf-8")
                )

            choices = result.get("choices", [])

            if not choices:
                raise LLMError("Provider tidak mengembalikan hasil.")

            content = choices[0].get("message", {}).get("content")

            if not isinstance(content, str) or not content.strip():
                raise LLMError("Jawaban AI kosong atau tidak valid.")

            return content.strip()

        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")

            if exc.code in RETRYABLE_STATUS and attempt < MAX_RETRIES:
                delay = _retry_delay(attempt, exc.headers)
                time.sleep(delay)
                continue

            raise LLMError(
                f"AI provider HTTP {exc.code}: {detail[:500]}"
            ) from exc

        except (socket.timeout, TimeoutError) as exc:
            if attempt < MAX_RETRIES:
                time.sleep(_retry_delay(attempt))
                continue

            raise LLMError(
                f"Server AI tidak merespons setelah "
                f"{MAX_RETRIES + 1} percobaan."
            ) from exc

        except urllib.error.URLError as exc:
            if attempt < MAX_RETRIES:
                time.sleep(_retry_delay(attempt))
                continue

            raise LLMError(
                f"Koneksi ke AI provider gagal: {exc.reason}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise LLMError(
                "Respons AI bukan JSON yang valid."
            ) from exc

    raise LLMError("Semua percobaan koneksi AI gagal.")
