import asyncio
import logging
import json
import base64
import os
from typing import Any, List, Optional, Tuple, Dict
from datetime import timedelta

from opensandbox import Sandbox
from opensandbox.config import ConnectionConfig
from opensandbox.models import WriteEntry
from code_interpreter import CodeInterpreter

from src.core.config import get_settings
from src.core.logger import logger
from deepagents.backends.sandbox import BaseSandbox, _READ_COMMAND_TEMPLATE
from deepagents.backends.protocol import (
    ExecuteResponse,
    FileUploadResponse,
    FileDownloadResponse,
    FileInfo,
    WriteResult,
)

class SandboxManager:
    """OpenSandbox 与 CodeInterpreter 实例的异步单例管理器。"""
    _instance: Optional['SandboxManager'] = None
    _lock: Optional[asyncio.Lock] = None
    
    @classmethod
    async def _get_class_lock(cls) -> asyncio.Lock:
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock
    
    def __init__(self):
        self.sandbox: Optional[Sandbox] = None
        self.interpreter: Optional[CodeInterpreter] = None
        self._sb_lock: Optional[asyncio.Lock] = None
        self._intp_lock: Optional[asyncio.Lock] = None

    def _get_config(self) -> ConnectionConfig:
        settings = get_settings()
        return ConnectionConfig(
            domain=settings.sandbox.url,
            api_key=settings.sandbox.api_key or "",
            request_timeout=timedelta(minutes=5),
            use_server_proxy=True,
        )

    async def _get_sb_lock(self) -> asyncio.Lock:
        if self._sb_lock is None:
            self._sb_lock = asyncio.Lock()
        return self._sb_lock

    async def _get_intp_lock(self) -> asyncio.Lock:
        if self._intp_lock is None:
            self._intp_lock = asyncio.Lock()
        return self._intp_lock

    @classmethod
    async def get_instance(cls) -> 'SandboxManager':
        if cls._instance is None:
            lock = await cls._get_class_lock()
            async with lock:
                if cls._instance is None:
                    cls._instance = SandboxManager()
        return cls._instance

    async def get_sandbox(self) -> Sandbox:
        lock = await self._get_sb_lock()
        async with lock:
            if self.sandbox is None:
                logger.info(f"Connecting to OpenSandbox at {self._get_config().domain}...")
                self.sandbox = await Sandbox.create(
                    image="opensandbox/code-interpreter:v1.0.2",
                    connection_config=self._get_config(),
                    entrypoint=["/opt/opensandbox/code-interpreter.sh"],
                    env={"PYTHON_VERSION": "3.11"}
                )
            return self.sandbox

    async def get_interpreter(self) -> CodeInterpreter:
        lock = await self._get_intp_lock()
        async with lock:
            if self.interpreter is None:
                logger.info("Initializing Code Interpreter Async...")
                sb = await self.get_sandbox()
                self.interpreter = await CodeInterpreter.create(sandbox=sb)
            return self.interpreter

    async def close(self):
        sb_lock = await self._get_sb_lock()
        intp_lock = await self._get_intp_lock()
        async with sb_lock:
            async with intp_lock:
                if self.sandbox:
                    await self.sandbox.close()
                    self.sandbox = None
                    self.interpreter = None

class OpenSandboxBackend(BaseSandbox):
    """深层集成 DeepAgents 的 OpenSandbox 后端实现。"""

    def __init__(self, url: str = None, api_key: str = None):
        # url and api_key are now handled by SandboxManager via Settings
        pass

    async def _get_sandbox(self) -> Sandbox:
        manager = await SandboxManager.get_instance()
        return await manager.get_sandbox()

    @property
    def id(self) -> str:
        return "opensandbox"

    # --- 协议接口实现 ---
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        try:
            asyncio.get_running_loop()
            return ExecuteResponse(output="Sync execute called from within active loop. Use aexecute.", exit_code=1)
        except RuntimeError:
            return asyncio.run(self.aexecute(command, timeout=timeout))

    def upload_files(self, files: List[Tuple[str, bytes]]) -> List[FileUploadResponse]:
        try:
            asyncio.get_running_loop()
            return [FileUploadResponse(path=f[0], error="permission_denied") for f in files]
        except RuntimeError:
            return asyncio.run(self.aupload_files(files))

    def download_files(self, paths: List[str]) -> List[FileDownloadResponse]:
        try:
            asyncio.get_running_loop()
            return [FileDownloadResponse(path=p, error="permission_denied") for p in paths]
        except RuntimeError:
            return asyncio.run(self.adownload_files(paths))

    # --- 异步重写 ---
    async def aexecute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        try:
            sb = await self._get_sandbox()
            execution = await sb.commands.run(command)
            stdout = "\n".join(msg.text for msg in execution.logs.stdout)
            stderr = "\n".join(msg.text for msg in execution.logs.stderr)
            return ExecuteResponse(
                output=f"{stdout}\n{stderr}".strip(),
                exit_code=getattr(execution, "exit_code", 0),
                truncated=False
            )
        except Exception as e:
            return ExecuteResponse(output=f"Error: {e}", exit_code=1)

    async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        payload = json.dumps({"path": file_path, "offset": int(offset), "limit": int(limit)})
        payload_b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        cmd = _READ_COMMAND_TEMPLATE.format(payload_b64=payload_b64)
        result = await self.aexecute(cmd)
        if result.exit_code != 0 or "Error: File not found" in result.output:
            return f"Error: File '{file_path}' not found"
        return result.output.rstrip()

    async def als_info(self, path: str) -> List[FileInfo]:
        path_b64 = base64.b64encode(path.encode("utf-8")).decode("ascii")
        cmd = f"python3 -c \"import os, json, base64; p = base64.b64decode('{path_b64}').decode('utf-8'); " + \
              "try: [print(json.dumps({'path': os.path.join(p, e.name), 'is_dir': e.is_dir()})) for e in os.scandir(p)] except: pass\" 2>/dev/null"
        result = await self.aexecute(cmd)
        infos = []
        for line in result.output.strip().split("\n"):
            if not line: continue
            try:
                d = json.loads(line)
                infos.append({"path": d["path"], "is_dir": d["is_dir"]})
            except: continue
        return infos

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        try:
            sb = await self._get_sandbox()
            await sb.files.write_files([WriteEntry(path=file_path, data=content)])
            return WriteResult(path=file_path)
        except Exception as e:
            return WriteResult(error=str(e))

    async def aupload_files(self, files: List[Tuple[str, bytes]]) -> List[FileUploadResponse]:
        try:
            sb = await self._get_sandbox()
            await sb.files.write_files([WriteEntry(path=f[0], data=f[1].decode('utf-8') if isinstance(f[1], bytes) else f[1]) for f in files])
            return [FileUploadResponse(path=f[0], error=None) for f in files]
        except Exception as e:
            return [FileUploadResponse(path=f[0], error=str(e)) for f in files]

    async def adownload_files(self, paths: List[str]) -> List[FileDownloadResponse]:
        responses = []
        sb = await self._get_sandbox()
        for path in paths:
            try:
                res = await sb.files.read_file(path)
                data = res.content if hasattr(res, 'content') else res
                responses.append(FileDownloadResponse(path=path, content=data if isinstance(data, bytes) else data.encode()))
            except:
                responses.append(FileDownloadResponse(path=path, error="file_not_found"))
        return responses

    async def close(self):
        manager = await SandboxManager.get_instance()
        await manager.close()
