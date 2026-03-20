import uuid
import json
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from src.api.deps import get_agent

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    user: Optional[str] = None  # Open WebUI 用户 ID

# 简单的内存会话映射：User ID -> Thread ID
# 生产环境下建议存储在 Redis 或数据库中
_session_map: Dict[str, str] = {}

@router.post("/completions")
async def chat_completions(request: ChatCompletionRequest):
    agent = get_agent()
    
    # 提取最后一条用户消息
    user_input = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_input = msg.content
            break
            
    if not user_input:
        raise HTTPException(status_code=400, detail="请求中未找到用户消息")

    # Debug: Log full request to find session identifiers
    logger.debug(f"Full Request Body: {request.model_dump_json()}")

    # 会话管理：尝试区分同一用户的不同对话
    user_id = request.user or "default-user"
    
    # 启发式：使用第一条消息的内容作为会话标识 (Conversation Key)
    # 如果只有一条消息，通常是新会话的开始
    first_msg_content = request.messages[0].content if request.messages else ""
    # 我们将 User ID 和第一条消息内容组合作为 Key
    import hashlib
    conv_key = hashlib.md5(f"{user_id}:{first_msg_content}".encode()).hexdigest()
    
    # 如果是新会话 (len == 1)，强制刷新该 conv_key 对应的 thread_id
    if len(request.messages) == 1:
        _session_map[conv_key] = f"thread-{uuid.uuid4().hex[:8]}"
        logger.info(f"New Conversation detected | Key: {conv_key} -> New Thread: {_session_map[conv_key]}")
    
    # 如果没有找到映射（可能是之前的长对话），则初始化一个
    if conv_key not in _session_map:
        _session_map[conv_key] = f"thread-{uuid.uuid4().hex[:8]}"
        
    thread_id = _session_map[conv_key]
    logger.info(f"API Request | User: {user_id} | ConvKey: {conv_key} | Thread: {thread_id} | Input: {user_input[:50]}...")

    if not request.stream:
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
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
        except Exception as e:
            logger.error(f"Chat API 错误: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        async def stream_generator():
            request_id = f"chatcmpl-{uuid.uuid4()}"
            created_time = int(time.time())
            
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
                
                yield f"data: {json.dumps({
                    'id': request_id, 'object': 'chat.completion.chunk', 'created': created_time,
                    'model': request.model, 'choices': [{'index': 0, 'delta': {}, 'finish_reason': 'stop'}]
                }, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Chat API 流错误: {e}")
                yield f"data: {json.dumps({'error': {'message': str(e)}})}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
