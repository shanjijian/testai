import os
import chainlit as cl
from src.core.agent import MainAgent
from src.core.config import get_settings
from src.core.logger import logger

# 设置项目根目录以便正确加载技能
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
    """处理用户消息。"""
    agent: MainAgent = cl.user_session.get("agent")
    
    # 使用 Chainlit 的 LangChain 回调处理器来可视化 Agent 的思考步骤
    cb = cl.AsyncLangchainCallbackHandler()
    
    try:
        # 运行 Agent
        response = await agent.async_run(
            user_input=message.content,
            user_id="chainlit_user",
            thread_id=cl.context.session.id,
            callbacks=[cb]
        )
        
        await cl.Message(content=response).send()
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        await cl.Message(content=f"⚠️ 抱歉，执行过程中发生错误: {str(e)}").send()
