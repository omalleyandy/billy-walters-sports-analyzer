"""Lightweight HTTP helper used by research/data collection modules."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx


class AsyncHTTPClient:
    """Small wrapper around httpx with sane defaults and logging hooks."""

    def __init__(self, timeout: int = 15) -> None:
        self._session: Optional[httpx.AsyncClient] = None
        self._timeout = timeout

    async def __aenter__(self) -> "AsyncHTTPClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _ensure_session(self) -> None:
        if self._session is None:
            limits = httpx.Limits(max_connections=20)
            self._session = httpx.AsyncClient(
                timeout=self._timeout, limits=limits, verify=False
            )

    async def get_json(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        await self._ensure_session()
        assert self._session is not None
        resp = await self._session.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def get_text(self, url: str, **kwargs: Any) -> str:
        await self._ensure_session()
        assert self._session is not None
        resp = await self._session.get(url, **kwargs)
        resp.raise_for_status()
        return resp.text

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
