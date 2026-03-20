import os
import time
import json
import uuid
import asyncio
from typing import List, Optional, Dict, Any, Union
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from loguru import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from contextlib import asynccontextmanager

from src.core.agent import MainAgent
from src.core.config import get_settings

# 全局 Agent 实例
agent: Optional[MainAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """管理应用生命周期负载。"""
    global agent
    settings = get_settings()
    agent = MainAgent(settings)
    # 可以在这里做一些预检查
    logger.info("🚀 TestAI OpenAI-compatible API server is starting...")
    yield
    logger.info("🛑 TestAI API server is shutting down...")

app = FastAPI(title="TestAI OpenAI-compatible API", lifespan=lifespan)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    max_tokens: Optional[int] = None
    user: Optional[str] = "default_user"

@app.get("/v1/models")
async def list_models():
    """返回模型列表。"""
    return {
        "object": "list",
        "data": [
            {
                "id": "testai-agent",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "testai"
            }
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """处理聊天补全请求。"""
    # 提取最后一条用户消息作为 Agent 输入
    user_input = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_input = msg.content
            break
    
    if not user_input:
        raise HTTPException(status_code=400, detail="No user message found in history")

    thread_id = f"api-{uuid.uuid4().hex[:8]}"
    user_id = request.user

    if not request.stream:
        # 非流式响应 (阻塞等待结果)
        try:
            response_text = await agent.async_run(
                user_input=user_input,
                user_id=user_id,
                thread_id=thread_id
            )
            return {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response_text
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0, # 简化处理
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except Exception as e:
            logger.error(f"API 异常: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # 流式响应 (SSE)
        async def event_generator():
            request_id = f"chatcmpl-{uuid.uuid4()}"
            created_time = int(time.time())
            
            # 发送角色开始标记
            yield f"data: {json.dumps({
                'id': request_id, 'object': 'chat.completion.chunk', 'created': created_time,
                'model': request.model, 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]
            }, ensure_ascii=False)}\n\n"

            try:
                async for token in agent.async_stream(
                    user_input=user_input,
                    user_id=user_id,
                    thread_id=thread_id
                ):
                    yield f"data: {json.dumps({
                        'id': request_id, 'object': 'chat.completion.chunk', 'created': created_time,
                        'model': request.model, 'choices': [{'index': 0, 'delta': {'content': token}, 'finish_reason': None}]
                    }, ensure_ascii=False)}\n\n"
                
                # 发送完成标记
                yield f"data: {json.dumps({
                    'id': request_id, 'object': 'chat.completion.chunk', 'created': created_time,
                    'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]
                }, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"API 滚动流异常: {e}")
                error_data = {"error": {"message": str(e), "type": "api_error"}}
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    # 默认运行在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)
