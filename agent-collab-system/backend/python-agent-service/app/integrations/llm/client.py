from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import httpx

from app.core.config import Settings, get_settings


@dataclass(slots=True)
class LLMClient:
    api_key: str
    base_url: str
    model: str
    request_path: str
    timeout_ms: int

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "LLMClient":
        resolved = settings or get_settings()
        return cls(
            api_key=resolved.resolved_llm_api_key,
            base_url=resolved.resolved_llm_base_url,
            model=resolved.llm_model,
            request_path=resolved.llm_request_path,
            timeout_ms=resolved.llm_timeout_ms,
        )

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    async def chat(self, *, messages: list[dict[str, str]], temperature: float = 0.3) -> str:
        if not self.enabled:
            raise RuntimeError("LLM_NOT_CONFIGURED")

        url = f"{self.base_url}{self.request_path if self.request_path.startswith('/') else f'/{self.request_path}'}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=self.timeout_ms / 1000) as client:
            response = await client.post(url, headers=headers, json=payload)
            _ = response.raise_for_status()
            raw_data = cast(object, response.json())

        payload_dict = cast(dict[str, object], raw_data) if isinstance(raw_data, dict) else {}
        choices = payload_dict.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
        raise RuntimeError("LLM_EMPTY_RESPONSE")
