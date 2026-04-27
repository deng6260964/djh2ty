import os
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings

# 允许的 MIME 类型白名单
ALLOWED_MIME_TYPES = {
    # 图片
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    # PDF
    "application/pdf",
    # Word
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Excel
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    # PowerPoint
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # 文本
    "text/plain",
}

# MIME 类型到文件类型映射
MIME_TO_FILE_TYPE = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/gif": "image",
    "image/webp": "image",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel": "excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "excel",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "ppt",
    "text/plain": "other",
}


async def save_upload_file(upload_file: UploadFile) -> tuple[str, str, int]:
    """
    保存上传文件
    Returns: (relative_path, mime_type, file_size)
    """
    # 验证文件类型
    content_type = upload_file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={"code": "FILE_TYPE_NOT_ALLOWED", "message": f"不支持的文件类型: {content_type}"}
        )

    # 读取文件内容（先读取后验证大小）
    content = await upload_file.read()
    file_size = len(content)

    # 验证文件大小
    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": "文件超过 50MB 限制"}
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail={"code": "FILE_EMPTY", "message": "文件内容为空"}
        )

    # 生成唯一文件名
    original_ext = Path(upload_file.filename or "file").suffix.lower()
    if not original_ext:
        # 根据 MIME 类型推断扩展名
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
            "application/msword": ".doc",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.ms-excel": ".xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "text/plain": ".txt",
        }
        original_ext = ext_map.get(content_type, ".bin")

    unique_name = f"{uuid.uuid4()}{original_ext}"
    year_month = datetime.now().strftime("%Y/%m")
    relative_path = f"resources/{year_month}/{unique_name}"

    # 确保目录存在
    upload_dir = settings.upload_dir_abs
    abs_path = Path(upload_dir) / relative_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    # 异步写入文件
    async with aiofiles.open(abs_path, "wb") as f:
        await f.write(content)

    return relative_path, content_type, file_size


def delete_file(relative_path: str) -> bool:
    """删除文件"""
    try:
        upload_dir = settings.upload_dir_abs
        abs_path = Path(upload_dir) / relative_path
        if abs_path.exists():
            abs_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_file_abs_path(relative_path: str) -> Optional[Path]:
    """获取文件绝对路径"""
    upload_dir = settings.upload_dir_abs
    abs_path = Path(upload_dir) / relative_path
    if abs_path.exists():
        return abs_path
    return None
