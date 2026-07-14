"""
Wikidot API 客户端

封装对 wikidot-api 后端服务的 HTTP 请求（JSON 与纯文本接口）。
"""

import json
from urllib.parse import urlencode

import aiohttp

API_BASE = "https://wiki-api.yaoonion.fun"


class WikidotApiClient:
    """与 wikidot-api 后端通信的客户端"""

    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url

    async def _request(self, path: str, params: dict | None = None) -> str:
        """发送 GET 请求，返回原始响应文本"""
        url = f"{self.base_url}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urlencode(clean)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"API HTTP {resp.status}: {text[:200]}")
                return await resp.text()

    async def get_json(self, path: str, params: dict | None = None) -> dict:
        """调用 JSON 接口并返回解析后的字典"""
        text = await self._request(path, params)
        return json.loads(text)

    async def get_text(self, path: str, params: dict | None = None) -> str:
        """调用纯文本接口"""
        return await self._request(path, params)
