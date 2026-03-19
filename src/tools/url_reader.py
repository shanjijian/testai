"""网页内容抓取与清洗工具。"""

import json
import asyncio
from typing import Optional
from curl_cffi.requests import AsyncSession
from src.utils.logging import log_tool_call


@log_tool_call
def read_url(url: str, max_length: int = 5000) -> str:
    """读取 URL 内容并返回纯文本摘要。"""
    return asyncio.run(_read_url_async(url, max_length))


async def _read_url_async(url: str, max_length: int = 5000) -> str:
    try:
        async with AsyncSession(impersonate="chrome") as session:
            response = await session.get(url, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                return json.dumps({
                    "url": url,
                    "error": f"请求失败，状态码: {response.status_code}"
                }, ensure_ascii=False)

            html = response.text
            text = _extract_text(html)

            # 提取标题
            title = _extract_title(html)

            return json.dumps({
                "url": url,
                "title": title,
                "content": text[:max_length],
                "truncated": len(text) > max_length,
                "total_length": len(text),
            }, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "url": url,
            "error": f"抓取失败: {str(e)}"
        }, ensure_ascii=False)


def _extract_title(html: str) -> str:
    """从 HTML 中提取 <title> 标签内容。"""
    import re
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_text(html: str) -> str:
    """从 HTML 中提取可读正文，去除脚本、样式和标签。"""
    import re
    # 移除 script 和 style 块
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # 移除 HTML 注释
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # 移除所有 HTML 标签
    text = re.sub(r"<[^>]+>", " ", html)
    # 解码 HTML 实体
    import html as html_module
    text = html_module.unescape(text)
    # 压缩空白
    text = re.sub(r"\s+", " ", text).strip()
    return text
