"""Lightweight HTTP helper used by research/data collection modules."""

from __future__ import annotations

from typing import Any, Dict, Optional

import aiohttp


class AsyncHTTPClient:
    """Small wrapper around aiohttp with sane defaults and logging hooks."""

    def __init__(self, timeout: int = 15) -> None:
        self._session: Optional[aiohttp.ClientSession] = None
        self._timeout = timeout

    async def __aenter__(self) -> "AsyncHTTPClient":
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _ensure_session(self) -> None:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._timeout)
            connector = aiohttp.TCPConnector(limit=20, ssl=False)
            self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)

    async def get_json(self, url: str, **kwargs: Any) -> Dict[str, Any]:
        await self._ensure_session()
        assert self._session is not None
        async with self._session.get(url, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_text(self, url: str, **kwargs: Any) -> str:
        await self._ensure_session()
        assert self._session is not None
        async with self._session.get(url, **kwargs) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None
