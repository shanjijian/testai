"""WebSerp 搜索工具。"""
import json
import asyncio
from typing import List, Optional
from curl_cffi.requests import AsyncSession
from webserp.search import search as search_async
from src.utils.logging import log_tool_call

@log_tool_call
def webserp_search(query: str, max_results: int = 5, visit_links: bool = False) -> str:
    """执行在线搜索，可选是否抓取网页正文。"""
    return asyncio.run(_webserp_search_async(query, max_results, visit_links))

async def _webserp_search_async(query: str, max_results: int = 5, visit_links: bool = False) -> str:
    try:
        # Perform search
        search_results = await search_async(query, max_results=max_results)
        
        if not search_results or not search_results.get("results"):
            return json.dumps({"query": query, "results": [], "message": "No results found."})

        results = search_results["results"]
        
        if visit_links:
            # Visit the top results in parallel to get content
            async with AsyncSession(impersonate="chrome") as session:
                tasks = []
                for res in results[:max_results]:
                    tasks.append(fetch_url_content(session, res["url"]))
                
                fetched_contents = await asyncio.gather(*tasks)
                
                for i, content in enumerate(fetched_contents):
                    if i < len(results):
                        results[i]["raw_content"] = content

        return json.dumps({
            "query": query,
            "number_of_results": len(results),
            "results": results
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})

async def fetch_url_content(session: AsyncSession, url: str) -> str:
    """获取指定 URL 的内容。"""
    try:
        response = await session.get(url, timeout=10)
        if response.status_code == 200:
            # Return a snippet of the page or the full text
            # For simplicity, returning first 2000 characters
            return response.text[:2000]
        else:
            return f"Failed to fetch content: Status {response.status_code}"
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

if __name__ == "__main__":
    # Quick test runner
    async def main():
        print(await webserp_search("Python news", max_results=2, visit_links=True))
    
    asyncio.run(main())
