from typing import Optional
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from src.core.config import get_settings
from src.core.logger import logger

class DatabaseManager:
    """PostgreSQL 数据库连接与持久化管理器 (单例)。"""
    _instance: Optional['DatabaseManager'] = None

    def __init__(self):
        settings = get_settings()
        logger.info(f"Connecting to PostgreSQL: {settings.database.url}")
        
        self.pool = AsyncConnectionPool(
            conninfo=settings.database.url,
            max_size=20,
            kwargs={"autocommit": True}
        )
        self.checkpointer = AsyncPostgresSaver(self.pool)
        self.store = AsyncPostgresStore(self.pool)

    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    async def close(self):
        """关闭数据库连接池。"""
        if self.pool:
            await self.pool.close()
