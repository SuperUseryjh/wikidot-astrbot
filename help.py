"""
帮助文本常量
"""

HELP_TEXT = (
    "📖 Wikidot 文章查询\n"
    "用法:\n"
    "  /wiki help                         - 显示本帮助\n"
    "  /wiki search <关键词> [-wiki 站点] - 搜索文章\n"
    "  /wiki <文章ID> [-wiki 站点]        - 查看文章详情\n"
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
