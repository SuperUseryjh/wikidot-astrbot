"""
Wikidot 文章查询插件

通过 /wiki 命令调用 wikidot-api 服务，搜索和查看 Wikidot 站点文章。
"""

import aiohttp
from urllib.parse import urlencode

from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import command
from astrbot.core.star import Star, Context

API_BASE = "https://wiki-api.yaoonion.fun"


class WikidotPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def _api_get(self, path: str, params: dict | None = None) -> dict:
        """调用 wikidot-api 的 JSON 接口"""
        url = f"{API_BASE}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urlencode(clean)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"API HTTP {resp.status}: {text[:200]}")
                return await resp.json()

    async def _api_text(self, path: str, params: dict | None = None) -> str:
        """调用 wikidot-api 的纯文本接口（如 /source）"""
        url = f"{API_BASE}{path}"
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, "")}
            if clean:
                url += "?" + urlencode(clean)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"API HTTP {resp.status}: {text[:200]}")
                return await resp.text()

    # ── 命令入口 ────────────────────────────────────────

    @command("wiki")
    async def wiki(self, event: AstrMessageEvent):
        """Wikidot 文章查询

        子命令: search, source, cats, tags, stats, help
        通用选项: -wiki <站点名>  指定目标站点（默认 mc-anomaly-archives）
        """
        # 使用 message_str 获取完整消息文本
        full_text = event.message_str.strip()
        # 去掉命令前缀（/wiki 或 /wiki@bot）
        for prefix in ("/wiki", "wiki"):
            if full_text.startswith(prefix):
                after = full_text[len(prefix):].strip()
                # 跳过 @bot 后缀（如 /wiki@bot）
                if after.startswith("@"):
                    space = after.find(" ")
                    after = after[space + 1:] if space != -1 else ""
                full_text = after
                break

        parts = full_text.split()
        if not parts:
            yield event.plain_result(self._help_text())
            return

        # 解析 -wiki 标志
        wiki_site = None
        filtered = []
        i = 0
        while i < len(parts):
            if parts[i] == "-wiki" and i + 1 < len(parts):
                wiki_site = parts[i + 1]
                i += 2
            else:
                filtered.append(parts[i])
                i += 1

        subcmd = filtered[0] if filtered else ""
        args = filtered[1:]

        params = {}
        if wiki_site:
            params["wiki"] = wiki_site

        try:
            if subcmd == "help":
                yield event.plain_result(self._help_text())
                return

            if subcmd in ("search", "s"):
                result = await self._cmd_search(args, params)
            elif subcmd in ("source", "src"):
                result = await self._cmd_source(args, params)
            elif subcmd == "cats":
                result = await self._cmd_cats(params)
            elif subcmd == "tags":
                result = await self._cmd_tags(params)
            elif subcmd == "stats":
                result = await self._cmd_stats(params)
            else:
                result = await self._cmd_detail(subcmd, params)

            if result:
                yield event.plain_result(result)

        except Exception as e:
            yield event.plain_result(f"❌ [{type(e).__name__}] {str(e) or '无详细信息'}")

    # ── 子命令实现（返回字符串，None 表示无输出）───────────

    async def _cmd_search(self, args: list[str], params: dict) -> str | None:
        if not args:
            return "用法: /wiki search <关键词> [-wiki 站点]"
        query = " ".join(args)
        p = {**params, "category": "*", "tags": query}
        data = await self._api_get("/api/pages", p)
        count = data.get("count", 0)
        pages = data.get("pages", [])
        if count == 0:
            return "没有找到相关文章"
        lines = [f"🔍 找到 {count} 篇文章："]
        for page in pages[:10]:
            title = page.get("title", page.get("fullname", "?"))
            rating = page.get("rating", 0)
            lines.append(f"  · {page['fullname']} — {title}  (评分: {rating})")
        if count > 10:
            lines.append(f"  ... 还有 {count - 10} 篇")
        return "\n".join(lines)

    async def _cmd_source(self, args: list[str], params: dict) -> str | None:
        if not args:
            return "用法: /wiki source <文章ID> [-wiki 站点]"
        fullname = args[0]
        text = await self._api_text(f"/api/pages/{fullname}/source", params)
        if len(text) > 2000:
            text = text[:2000] + "\n\n... (内容过长已截断)"
        return f"📄 {fullname} 源代码:\n\n{text}"

    async def _cmd_cats(self, params: dict) -> str | None:
        data = await self._api_get("/api/categories", params)
        cats = data.get("categories", [])
        if not cats:
            return "没有找到分类"
        lines = [f"📂 分类列表 ({len(cats)} 个):"]
        for c in cats:
            lines.append(f"  · {c}")
        return "\n".join(lines)

    async def _cmd_tags(self, params: dict) -> str | None:
        data = await self._api_get("/api/tags", params)
        tags = data.get("tags", [])
        if not tags:
            return "没有找到标签"
        lines = [f"🏷️ 标签列表 ({len(tags)} 个):"]
        for t in tags[:50]:
            lines.append(f"  · {t}")
        msg = "\n".join(lines)
        if len(tags) > 50:
            msg += f"\n  ... 还有 {len(tags) - 50} 个标签"
        return msg

    async def _cmd_stats(self, params: dict) -> str | None:
        data = await self._api_get("/api/stats", params)
        lines = [
            "📊 站点统计",
            f"  总文章: {data.get('total_pages', 0)}",
            f"  总分类: {data.get('total_categories', 0)}",
            f"  总大小: {data.get('total_size_bytes', 0)} bytes",
            f"  总评分: {data.get('total_votes', 0)}",
            f"  总评论: {data.get('total_comments', 0)}",
        ]
        return "\n".join(lines)

    async def _cmd_detail(self, fullname: str, params: dict) -> str | None:
        data = await self._api_get(f"/api/pages/{fullname}", params)
        title = data.get("title", fullname)
        category = data.get("category", "?")
        tags_list = data.get("tags", [])
        tags = ", ".join(tags_list) if tags_list else "无"
        rating = data.get("rating", 0)
        votes = data.get("votes_count", 0)
        source = data.get("source", "")

        lines = [
            f"📄 {fullname}",
            f"  标题: {title}",
            f"  分类: {category}",
            f"  标签: {tags}",
            f"  评分: {rating} (共 {votes} 票)",
        ]
        if source:
            preview = source[:500]
            if len(source) > 500:
                preview += "\n  ... (内容过长已截断)"
            lines.append(f"  内容预览:\n{preview}")
        return "\n".join(lines)

    # ── 帮助文本 ────────────────────────────────────────

    @staticmethod
    def _help_text() -> str:
        return (
            "📖 Wikidot 文章查询\n"
            "用法:\n"
            "  /wiki help                        - 显示本帮助\n"
            "  /wiki search <关键词> [-wiki 站点] - 搜索文章\n"
            "  /wiki <文章ID> [-wiki 站点]       - 查看文章详情\n"
            "  /wiki source <文章ID> [-wiki 站点] - 查看 Wiki 源代码\n"
            "  /wiki cats [-wiki 站点]            - 分类列表\n"
            "  /wiki tags [-wiki 站点]            - 标签列表\n"
            "  /wiki stats [-wiki 站点]           - 站点统计\n\n"
            "可选参数 -wiki 指定目标站点，默认 mc-anomaly-archives\n"
            "示例:\n"
            "  /wiki search 原创\n"
            "  /wiki search SCP -wiki scp-wiki\n"
            "  /wiki co-1\n"
            "  /wiki source co-1"
        )
