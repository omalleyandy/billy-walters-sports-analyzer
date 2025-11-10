from __future__ import annotations
import os
import json
import random
from typing import Any, Dict, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx
import pandas as pd

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17 Safari/605.1.15",
]


def user_agent() -> str:
    if os.getenv("USER_AGENT_ROTATION", "true").lower() == "true":
        return random.choice(UA_POOL)
    return UA_POOL[0]


def to_curl(
    method: str, url: str, headers: Dict[str, str], body: Optional[bytes]
) -> str:
    parts = [f"curl -X {method.upper()} '{url}'"]
    for k, v in headers.items():
        if k.lower() in {"cookie"}:
            continue
        parts.append(f"-H '{k}: {v}'")
    if body:
        try:
            parts.append(f"--data-raw '{body.decode('utf-8')}'")
        except Exception:
            parts.append("--data-binary '<binary>'")
    return " \\\n  ".join(parts)


def to_fetch(
    method: str, url: str, headers: Dict[str, str], body: Optional[bytes]
) -> str:
    hdrs = {k: v for k, v in headers.items() if k.lower() != "cookie"}
    body_s: str | None = None
    if body:
        try:
            body_s = body.decode("utf-8")
        except Exception:
            body_s = None
    config = {"method": method.upper(), "headers": hdrs}
    if body_s:
        config["body"] = body_s
    return f"fetch('{url}', {json.dumps(config, indent=2)})"


def df_export(df: pd.DataFrame, base: str, out_dir: str) -> dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    paths = {
        "csv": os.path.join(out_dir, f"{base}.csv"),
        "json": os.path.join(out_dir, f"{base}.json"),
        "parquet": os.path.join(out_dir, f"{base}.parquet"),
    }
    df.to_csv(paths["csv"], index=False)
    df.to_json(paths["json"], orient="records")
    df.to_parquet(paths["parquet"], index=False)
    return paths


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=6),
    retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
)
def replay_get(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    timeout = float(os.getenv("REQUEST_TIMEOUT_S", "20"))
    proxies = (
        os.getenv("ALL_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    )
    hdrs = {"user-agent": user_agent(), "accept": "application/json, text/plain, */*"}
    if headers:
        hdrs.update(headers)
    with httpx.Client(proxies=proxies, timeout=timeout, headers=hdrs) as client:
        return client.get(url, params=params)
