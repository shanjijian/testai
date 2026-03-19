import os
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path 以确保可以导入 src 模块
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 确保当前工作目录是项目根目录，以便正确加载技能等相对路径资源
os.chdir(project_root)

import chainlit as cl
from src.core.agent import MainAgent
from src.core.config import get_settings
from src.core.logger import logger

@cl.on_chat_start
async def start():
    """初始化会话，创建 Agent 实例。"""
    try:
        settings = get_settings()
        agent = MainAgent(settings)
        cl.user_session.set("agent", agent)
        
        await cl.Message(content="👋 你好！我是 TestAI 智能助手。我已经准备好协助您进行研究、编写代码或执行任务。").send()
    except Exception as e:
        logger.error(f"Failed to start Chainlit session: {e}")
        await cl.Message(content=f"❌ 启动失败: {str(e)}").send()

@cl.on_message
async def main(message: cl.Message):
    """处理用户消息并流式返回响应。"""
    agent: MainAgent = cl.user_session.get("agent")
    
    # 使用 Chainlit 的 LangChain 回调处理器来可视化 Agent 的思考步骤 (如工具调用)
    cb = cl.AsyncLangchainCallbackHandler()
    
    # 创建一个空消息用于流式输出
    msg = cl.Message(content="")
    
    try:
        # 运行 Agent 流式输出
        async for token in agent.async_stream(
            user_input=message.content,
            user_id="chainlit_user",
            thread_id=cl.context.session.id,
            callbacks=[cb]
        ):
            await msg.stream_token(token)
        
        # 发送最终形成的完整消息
        await msg.send()
        
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        # 如果流式过程中出错，确保关闭消息状态
        if not msg.content:
            await cl.Message(content=f"⚠️ 抱歉，执行过程中发生错误: {str(e)}").send()
        else:
            await cl.Message(content=f"\n\n[错误断开: {str(e)}]").send()
