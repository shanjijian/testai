import logging
import asyncio
from typing import Optional, Dict, Any

from src.infrastructure.sandbox import SandboxManager
from code_interpreter import SupportedLanguage
from src.utils.logging import log_tool_call

logger = logging.getLogger(__name__)

# 沙箱工具实现

@log_tool_call
async def sandbox_execute_command(command: str) -> Dict[str, Any]:
    """在沙箱执行 Shell 命令。"""
    try:
        manager = await SandboxManager.get_instance()
        sb = await manager.get_sandbox()
        execution = await sb.commands.run(command)
        
        stdout = "\n".join(msg.text for msg in execution.logs.stdout)
        stderr = "\n".join(msg.text for msg in execution.logs.stderr)
        
        return {
            "success": True,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": getattr(execution, "exit_code", 0)
        }
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return {"success": False, "error": str(e)}

@log_tool_call
async def sandbox_run_python(code: str) -> Dict[str, Any]:
    """在沙箱执行 Python 代码。"""
    try:
        manager = await SandboxManager.get_instance()
        interpreter = await manager.get_interpreter()
        execution = await interpreter.codes.run(code, language=SupportedLanguage.PYTHON)
        
        stdout = "\n".join(r.text for r in execution.result if hasattr(r, 'text')) if execution.result else ""
        
        return {
            "success": True,
            "result": stdout,
            "stdout": stdout,
            "logs": [str(l) for l in execution.logs.stdout] if execution.logs else []
        }
    except Exception as e:
        logger.error(f"Python execution failed: {e}")
        return {"success": False, "error": str(e)}

@log_tool_call
async def sandbox_write_file(path: str, content: str) -> Dict[str, Any]:
    """向沙箱写入文件。"""
    from opensandbox.models import WriteEntry
    try:
        manager = await SandboxManager.get_instance()
        sb = await manager.get_sandbox()
        await sb.files.write_files([WriteEntry(path=path, data=content)])
        return {"success": True, "message": f"文件已写入: {path}"}
    except Exception as e:
        logger.error(f"File write failed: {e}")
        return {"success": False, "error": str(e)}

@log_tool_call
async def sandbox_read_file(path: str) -> Dict[str, Any]:
    """从沙箱读取文件。"""
    try:
        manager = await SandboxManager.get_instance()
        sb = await manager.get_sandbox()
        res = await sb.files.read_file(path)
        content = res.content if hasattr(res, 'content') else res
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        return {"success": True, "content": content}
    except Exception as e:
        logger.error(f"File read failed: {e}")
        return {"success": False, "error": str(e)}
