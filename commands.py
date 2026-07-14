"""
子命令实现

每个函数对应一个 /wiki 子命令，接收 WikidotApiClient 实例和参数，
返回纯文本结果（或 None）。
"""

from .api import WikidotApiClient


async def cmd_search(
    client: WikidotApiClient, args: list[str], params: dict
) -> str | None:
    """搜索文章（按标签匹配）"""
    if not args:
        return "用法: /wiki search <关键词> [-wiki 站点]"
    query = " ".join(args)
    p = {**params, "category": "*", "tags": query}
    data = await client.get_json("/api/pages", p)
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


async def cmd_source(
    client: WikidotApiClient, args: list[str], params: dict
) -> str | None:
    """查看文章 Wiki 源代码"""
    if not args:
        return "用法: /wiki source <文章ID> [-wiki 站点]"
    fullname = args[0]
    text = await client.get_text(f"/api/pages/{fullname}/source", params)
    if len(text) > 2000:
        text = text[:2000] + "\n\n... (内容过长已截断)"
    return f"📄 {fullname} 源代码:\n\n{text}"


async def cmd_detail(
    client: WikidotApiClient, fullname: str, params: dict
) -> str | None:
    """查看文章详情"""
    data = await client.get_json(f"/api/pages/{fullname}", params)
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


async def cmd_cats(client: WikidotApiClient, params: dict) -> str | None:
    """列出全部分类"""
    data = await client.get_json("/api/categories", params)
    cats = data.get("categories", [])
    if not cats:
        return "没有找到分类"
    lines = [f"📂 分类列表 ({len(cats)} 个):"]
    for c in cats:
        lines.append(f"  · {c}")
    return "\n".join(lines)


async def cmd_tags(client: WikidotApiClient, params: dict) -> str | None:
    """列出全部标签"""
    data = await client.get_json("/api/tags", params)
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


async def cmd_stats(client: WikidotApiClient, params: dict) -> str | None:
    """查看站点统计"""
    data = await client.get_json("/api/stats", params)
    lines = [
        "📊 站点统计",
        f"  总文章: {data.get('total_pages', 0)}",
        f"  总分类: {data.get('total_categories', 0)}",
        f"  总大小: {data.get('total_size_bytes', 0)} bytes",
        f"  总评分: {data.get('total_votes', 0)}",
        f"  总评论: {data.get('total_comments', 0)}",
    ]
    return "\n".join(lines)
