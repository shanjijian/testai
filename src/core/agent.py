"""核心代理实现类。"""

import os
from pathlib import Path
from typing import Optional
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from deepagents import create_deep_agent
from src.core.config import get_settings, Settings
from src.core.llm import custom_llm
from src.core.logger import logger
from src.core.prompts import MainPrompt
from src.agents.research_subagent import research_subagent
from src.agents.code_exec_subagent import code_exec_subagent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.store import StoreBackend
from src.infrastructure.sandbox import OpenSandboxBackend
from src.infrastructure.database import DatabaseManager
from src.tools.tencent_cos import upload_to_cos

class MainAgent:
    """由 DeepAgents 驱动的主代理，协调子代理与工具。"""

    def __init__(
        self,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.prompt_manager = MainPrompt()
        model = custom_llm(self.settings)
        system_prompt = self.prompt_manager.get_main_prompt()
        main_skills_dir = self.settings.skills.main_dir
        skill_paths = []
        if main_skills_dir:
            abs_skills_path = Path(os.getcwd()) / main_skills_dir
            if abs_skills_path.exists() and abs_skills_path.is_dir():
                skill_paths = [
                    str(p.absolute())
                    for p in abs_skills_path.iterdir()
                    if p.is_dir() and not p.name.startswith(".")
                ]
        
        logger.debug(f"Loaded skills: {skill_paths}")

        # 基础设施初始化
        db_manager = DatabaseManager.get_instance()
        self.checkpointer = db_manager.checkpointer
        self.store = db_manager.store
        
        # 配置复合后端：支持沙箱执行、本地技能读取与数据库持久化
        sandbox_backend = OpenSandboxBackend(
            url=self.settings.sandbox.url, 
            api_key=self.settings.sandbox.api_key
        )
        filesystem_backend = FilesystemBackend(root_dir="./skills", virtual_mode=True)
        store_backend = StoreBackend(
            runtime=None, # create_deep_agent 会自动设置 runtime
            namespace=lambda ctx: ("users", ctx.runtime.config.get("configurable", {}).get("user_id", "default_user"), "history")
        )
        
        composite_backend = CompositeBackend(
            default=sandbox_backend,
            routes={
                "/skills/": filesystem_backend,
                "/conversation_history/": store_backend
            }
        )

        self.agent = create_deep_agent(
            model=model,
            system_prompt=system_prompt,
            skills=skill_paths,
            subagents=[research_subagent, code_exec_subagent],
            backend=composite_backend,
            tools=[upload_to_cos],
            checkpointer=self.checkpointer,
            store=self.store,
            debug=True,
        )


    async def async_run(self, user_input: str, user_id: str = "default_user", thread_id: str = "default_thread", callbacks: Optional[list] = None):
        """执行 Agent 并返回最终回复字符串。"""
        # 确保基础设施就绪
        await self.checkpointer.setup()
        await self.store.setup()
        
        final_callbacks = self._get_callbacks(callbacks)
        
        logger.info(f"🚦 [MainAgent] Starting to process user input (User: {user_id}, Thread: {thread_id}): {user_input[:100]}...")
        
        config = {
            "configurable": {"thread_id": thread_id, "user_id": user_id},
            "callbacks": final_callbacks,
            "recursion_limit": self.settings.recursion_limit,
        }
        
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config
        )
        return result["messages"][-1].content

    async def async_stream(self, user_input: str, user_id: str = "default_user", thread_id: str = "default_thread", callbacks: Optional[list] = None):
        """流式执行 Agent，生成 Token 序列。"""
        # 确保基础设施就绪
        await self.checkpointer.setup()
        await self.store.setup()
        
        final_callbacks = self._get_callbacks(callbacks)
        
        logger.info(f"🌊 [MainAgent] Starting streaming process (User: {user_id}, Thread: {thread_id})...")
        
        config = {
            "configurable": {"thread_id": thread_id, "user_id": user_id},
            "callbacks": final_callbacks,
            "recursion_limit": self.settings.recursion_limit,
        }
        
        async for event in self.agent.astream_events(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
            version="v2"
        ):
            kind = event["event"]
            # 捕获聊天模型输出的 Token 块
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content

    def _get_callbacks(self, extra_callbacks: Optional[list] = None) -> list:
        """获取合并后的回调处理器列表。"""
        callbacks = []
        if self.settings.langfuse.public_key and self.settings.langfuse.secret_key:
            langfuse_client = Langfuse(
                public_key=self.settings.langfuse.public_key,
                secret_key=self.settings.langfuse.secret_key,
                host=self.settings.langfuse.base_url,
            )
            handler = CallbackHandler(public_key=self.settings.langfuse.public_key)
            handler.client = langfuse_client
            callbacks.append(handler)
        
        if extra_callbacks:
            callbacks.extend(extra_callbacks)
        return callbacks
