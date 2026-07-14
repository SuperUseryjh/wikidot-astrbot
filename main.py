"""
Wikidot 文章查询插件

通过 /wiki 命令调用 wikidot-api 服务，搜索和查看 Wikidot 站点文章。
"""

from astrbot.api.event import AstrMessageEvent
from astrbot.api.event.filter import command
from astrbot.core.star import Star, Context

from .api import WikidotApiClient
from .commands import (
    cmd_search,
    cmd_source,
    cmd_detail,
    cmd_cats,
    cmd_tags,
    cmd_stats,
)
from .help import HELP_TEXT


class WikidotPlugin(Star):
    """AstrBot 插件 - Wikidot 文章查询"""

    def __init__(self, context: Context):
        super().__init__(context)
        self.client = WikidotApiClient()

    @command("wiki")
    async def wiki(self, event: AstrMessageEvent):
        """Wikidot 文章查询命令入口"""
        full_text = event.message_str.strip()
        # 去掉命令前缀（/wiki 或 /wiki@bot）
        for prefix in ("/wiki", "wiki"):
            if full_text.startswith(prefix):
                after = full_text[len(prefix) :].strip()
                # 跳过 @bot 后缀
                if after.startswith("@"):
                    space = after.find(" ")
                    after = after[space + 1 :] if space != -1 else ""
                full_text = after
                break

        parts = full_text.split()
        if not parts:
            yield event.plain_result(HELP_TEXT)
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
            result = await self._route(subcmd, args, params)
            yield event.plain_result(result)
        except Exception as e:
            yield event.plain_result(
                f"❌ [{type(e).__name__}] {str(e) or '无详细信息'}"
            )

    async def _route(self, subcmd: str, args: list[str], params: dict) -> str:
        """路由到对应的子命令处理器"""
        if subcmd == "help":
            return HELP_TEXT

        if subcmd in ("search", "s"):
            return await cmd_search(self.client, args, params)
        if subcmd in ("source", "src"):
            return await cmd_source(self.client, args, params)
        if subcmd == "cats":
            return await cmd_cats(self.client, params)
        if subcmd == "tags":
            return await cmd_tags(self.client, params)
        if subcmd == "stats":
            return await cmd_stats(self.client, params)

        return await cmd_detail(self.client, subcmd, params)
