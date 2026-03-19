"""TestAI 代理 CLI 入口脚本。"""
import asyncio
import argparse
from src.core.agent import MainAgent
from src.core.logger import logger
from dotenv import load_dotenv

async def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="TestAI Agent CLI")
    parser.add_argument(
        "--query", 
        type=str, 
        default="我是谁？", 
        help="待测试的查询语句"
    )
    args = parser.parse_args()
    
    main_agent = MainAgent()
    logger.info(f"Starting agent with query: {args.query}")
    
    result = await main_agent.async_run(
        user_input=args.query,
        user_id="Tom",
        thread_id="Tom-Thread-1"
    )
    logger.info(f"Agent processing complete.")
    logger.info(f"Result:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
