from langchain_openai import ChatOpenAI
from src.core.config import Settings

def custom_llm(settings: Settings):
    """根据 Settings 动态初始化 LLM 实例。"""
    return ChatOpenAI(
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
        temperature=settings.llm.temperature,
        timeout=settings.llm.timeout,
    )