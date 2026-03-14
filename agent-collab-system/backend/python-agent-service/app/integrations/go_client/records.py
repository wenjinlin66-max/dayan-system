from __future__ import annotations

import httpx
from typing import cast

from app.runtime.models import JsonValue


class GoRecordsClient:
    """Client for Go generic records API."""

    base_url: str
    timeout: float

    def __init__(self, base_url: str, timeout_ms: int = 8000) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_ms / 1000

    async def create_record(self, table_id: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return await self._request("POST", f"/api/v1/records/{table_id}", payload)

    async def update_record(self, table_id: str, record_id: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return await self._request("PUT", f"/api/v1/records/{table_id}/{record_id}", payload)

    async def query_records(self, table_id: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        return await self._request("POST", f"/api/v1/records/{table_id}/query", payload)

    async def _request(self, method: str, path: str, payload: dict[str, JsonValue]) -> dict[str, JsonValue]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.request(method, path, json=payload)
            _ = response.raise_for_status()
            data = cast(object, response.json())
        if not isinstance(data, dict):
            return {"status": "invalid_response"}
        return {
            key: cast(JsonValue, value)
            for key, value in cast(dict[object, object], data).items()
            if isinstance(key, str)
        }
