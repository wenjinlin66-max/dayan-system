from __future__ import annotations

from dataclasses import dataclass
import json
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
            try:
                raw_data = cast(object, response.json())
            except ValueError as exc:
                raise RuntimeError("LLM_INVALID_RESPONSE_FORMAT") from exc

        payload_dict = cast(dict[str, object], raw_data) if isinstance(raw_data, dict) else {}
        choices = payload_dict.get("choices")
        if isinstance(choices, list) and choices:
            first = cast(object, choices[0])
            if isinstance(first, dict):
                first_dict = cast(dict[str, object], first)
                message = first_dict.get("message")
                if isinstance(message, dict):
                    message_dict = cast(dict[str, object], message)
                    content = message_dict.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
        raise RuntimeError("LLM_EMPTY_RESPONSE")

    async def chat_json(self, *, messages: list[dict[str, str]], temperature: float = 0.2) -> dict[str, object]:
        content = await self.chat(messages=messages, temperature=temperature)
        return self._extract_json_object(content)

    @staticmethod
    def _extract_json_object(content: str) -> dict[str, object]:
        candidates = [content.strip()]
        if "```json" in content:
            for segment in content.split("```json")[1:]:
                candidates.append(segment.split("```", 1)[0].strip())
        if "```" in content:
            for segment in content.split("```")[1::2]:
                candidates.append(segment.strip())

        decoder = json.JSONDecoder()
        for candidate in candidates:
            if not candidate:
                continue
            try:
                parsed = cast(object, json.loads(candidate))
            except json.JSONDecodeError:
                start = candidate.find("{")
                if start < 0:
                    continue
                try:
                    decoded = cast(tuple[object, int], decoder.raw_decode(candidate[start:]))
                    parsed = decoded[0]
                except json.JSONDecodeError:
                    continue
            if isinstance(parsed, dict):
                return cast(dict[str, object], parsed)
        raise RuntimeError("LLM_INVALID_JSON_RESPONSE")
