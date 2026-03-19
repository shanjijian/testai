"""Tavily 互联网搜索工具。"""

import os
from typing import Literal
from tavily import TavilyClient
from src.utils.logging import log_tool_call


@log_tool_call
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
) -> dict:
    """执行互联网搜索。"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"error": "未设置 TAVILY_API_KEY 环境变量。"}

    client = TavilyClient(api_key=api_key)
    return client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )