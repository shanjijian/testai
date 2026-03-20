import os
from typing import Optional
from qcloud_cos import CosConfig, CosS3Client
from src.core.config import get_settings
from src.utils.logging import log_tool_call

from src.infrastructure.sandbox import SandboxManager

@log_tool_call
async def upload_to_cos(
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    cos_path: Optional[str] = None,
    expire_seconds: int = 3600
) -> str:
    """上传文件或内容到腾讯云 COS 并返回下载链接。"""
    settings = get_settings()
    
    if not all([settings.storage.cos_secret_id, settings.storage.cos_secret_key, settings.storage.cos_bucket]):
        raise ValueError("Tencent COS credentials (secret_id, secret_key, bucket) are not configured.")
        
    config = CosConfig(
        Region=settings.storage.cos_region,
        SecretId=settings.storage.cos_secret_id,
        SecretKey=settings.storage.cos_secret_key,
        Scheme="https"
    )
    client = CosS3Client(config)
    
    if cos_path is None:
        if file_path:
            cos_path = os.path.basename(file_path)
        else:
            cos_path = "upload.txt"

    # 1. 优先使用提供的内存内容
    if content is not None:
        client.put_object(
            Bucket=settings.storage.cos_bucket,
            Body=content,
            Key=cos_path
        )
    # 2. 尝试从本地（宿主机）读取
    elif file_path and os.path.exists(file_path):
        client.upload_file(
            Bucket=settings.storage.cos_bucket,
            LocalFilePath=file_path,
            Key=cos_path
        )
    # 3. 尝试从沙箱读取
    elif file_path:
        try:
            manager = await SandboxManager.get_instance()
            sb = await manager.get_sandbox()
            res = await sb.files.read_file(file_path)
            body = res.content if hasattr(res, 'content') else res
            
            client.put_object(
                Bucket=settings.storage.cos_bucket,
                Body=body,
                Key=cos_path
            )
        except Exception as e:
            raise FileNotFoundError(f"File not found on host or sandbox: {file_path}. Error: {str(e)}")
    else:
        raise ValueError("Either file_path or content must be provided.")
    
    # 生成带签名的下载链接
    download_url = client.get_presigned_url(
        Bucket=settings.storage.cos_bucket,
        Key=cos_path,
        Method="GET",
        Expired=expire_seconds
    )
    
    return download_url
