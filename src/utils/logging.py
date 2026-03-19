import functools
import asyncio
import json
from typing import Callable
from src.core.logger import logger

def log_tool_call(func: Callable) -> Callable:
    """装饰器：记录工具调用的输入参数与返回结果。"""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        tool_name = func.__name__
        try:
            args_str = json.dumps(args, ensure_ascii=False) if args else ""
            kwargs_str = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
        except (TypeError, OverflowError):
            args_str = repr(args) if args else ""
            kwargs_str = repr(kwargs) if kwargs else ""

        logger.info(f"🛠️ [Tool Call] {tool_name} | Args: {args_str} | Kwargs: {kwargs_str}")
        
        try:
            result = await func(*args, **kwargs)
            try:
                result_str = json.dumps(result, ensure_ascii=False)
            except (TypeError, OverflowError):
                result_str = repr(result)
            
            if len(result_str) > 2000:
                result_str = result_str[:2000] + "... (truncated)"
                
            logger.info(f"✅ [Tool Return] {tool_name} | Result: {result_str}")
            return result
        except Exception as e:
            logger.error(f"❌ [Tool Error] {tool_name} | Error: {str(e)}")
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tool_name = func.__name__
        try:
            args_str = json.dumps(args, ensure_ascii=False) if args else ""
            kwargs_str = json.dumps(kwargs, ensure_ascii=False) if kwargs else ""
        except (TypeError, OverflowError):
            args_str = repr(args) if args else ""
            kwargs_str = repr(kwargs) if kwargs else ""

        logger.info(f"🛠️ [Tool Call] {tool_name} | Args: {args_str} | Kwargs: {kwargs_str}")
        
        try:
            result = func(*args, **kwargs)
            try:
                result_str = json.dumps(result, ensure_ascii=False)
            except (TypeError, OverflowError):
                result_str = repr(result)
                
            if len(result_str) > 2000:
                result_str = result_str[:2000] + "... (truncated)"

            logger.info(f"✅ [Tool Return] {tool_name} | Result: {result_str}")
            return result
        except Exception as e:
            logger.error(f"❌ [Tool Error] {tool_name} | Error: {str(e)}")
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
