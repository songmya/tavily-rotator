import os
import time
import asyncio
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field


RAW_KEYS = os.getenv("TAVILY_API_KEYS", "")
TAVILY_API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

APP_API_TOKEN = os.getenv("APP_API_TOKEN", "").strip()
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
KEY_COOLDOWN_SECONDS = int(os.getenv("KEY_COOLDOWN_SECONDS", "60"))

# Tavily Search endpoint
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

if not TAVILY_API_KEYS:
    raise RuntimeError("环境变量 TAVILY_API_KEYS 未设置，无法启动服务。")


app = FastAPI(
    title="NAS Tavily Gateway",
    description="多 Tavily API Key 轮询网关",
    version="1.0.0",
)


class TavilySearchRequest(BaseModel):
    query: str = Field(..., description="搜索关键词")
    topic: Optional[str] = None
    search_depth: Optional[str] = None
    max_results: Optional[int] = None
    include_answer: Optional[bool] = None
    include_raw_content: Optional[bool] = None
    include_images: Optional[bool] = None
    include_image_descriptions: Optional[bool] = None
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    days: Optional[int] = None
    time_range: Optional[str] = None
    country: Optional[str] = None
    chunks_per_source: Optional[int] = None


class KeyPool:
    def __init__(self, keys: List[str], cooldown_seconds: int = 60):
        self.keys = keys
        self.cooldown_seconds = cooldown_seconds
        self.index = 0
        self.lock = asyncio.Lock()
        self.unhealthy_until: Dict[str, float] = {}

    async def get_next_key(self) -> str:
        async with self.lock:
            now = time.time()
            total = len(self.keys)

            # 优先找健康 key
            for _ in range(total):
                key = self.keys[self.index]
                self.index = (self.index + 1) % total
                if self.unhealthy_until.get(key, 0) <= now:
                    return key

            # 如果都在冷却，也返回一个，避免完全阻塞
            key = self.keys[self.index]
            self.index = (self.index + 1) % total
            return key

    async def mark_unhealthy(self, key: str):
        async with self.lock:
            self.unhealthy_until[key] = time.time() + self.cooldown_seconds

    async def get_status(self) -> Dict[str, Any]:
        now = time.time()
        keys = []
        for k in self.keys:
            state = "healthy" if self.unhealthy_until.get(k, 0) <= now else "cooldown"
            masked = f"{k[:8]}...{k[-4:]}" if len(k) > 12 else "***"
            keys.append({"key": masked, "state": state})
        return {"total_keys": len(self.keys), "keys": keys}


key_pool = KeyPool(TAVILY_API_KEYS, KEY_COOLDOWN_SECONDS)


def verify_gateway_token(x_api_key: Optional[str]):
    if APP_API_TOKEN:
        if not x_api_key or x_api_key != APP_API_TOKEN:
            raise HTTPException(status_code=401, detail="无效的网关令牌")


@app.get("/health")
async def health():
    return {"ok": True, "service": "nas-tavily-gateway"}


@app.get("/pool-status")
async def pool_status(x_api_key: Optional[str] = Header(default=None)):
    verify_gateway_token(x_api_key)
    return await key_pool.get_status()


@app.post("/search")
async def search(body: TavilySearchRequest, x_api_key: Optional[str] = Header(default=None)):
    verify_gateway_token(x_api_key)

    payload = body.model_dump(exclude_none=True)
    errors = []
    max_attempts = len(TAVILY_API_KEYS)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for attempt in range(max_attempts):
            api_key = await key_pool.get_next_key()

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            try:
                resp = await client.post(
                    TAVILY_SEARCH_URL,
                    headers=headers,
                    json=payload,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    data["_gateway"] = {
                        "attempt": attempt + 1,
                        "message": "success",
                    }
                    return data

                # 这些错误适合切 key 再试
                if resp.status_code in (401, 429, 432, 433, 500, 502, 503, 504):
                    await key_pool.mark_unhealthy(api_key)
                    errors.append({
                        "attempt": attempt + 1,
                        "status_code": resp.status_code,
                        "detail": resp.text[:500],
                    })
                    continue

                raise HTTPException(
                    status_code=resp.status_code,
                    detail={
                        "message": "Tavily 返回了非重试错误",
                        "response": resp.text,
                    },
                )

            except httpx.RequestError as e:
                await key_pool.mark_unhealthy(api_key)
                errors.append({
                    "attempt": attempt + 1,
                    "status_code": "network_error",
                    "detail": str(e),
                })
                continue

    raise HTTPException(
        status_code=503,
        detail={
            "message": "所有 Tavily API Key 都尝试失败",
            "errors": errors,
        },
    )