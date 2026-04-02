"""アップロード関連スキーマ。"""

from __future__ import annotations

from datetime import datetime

from app.schemas.common import AppSchema


class UploadedImageInfo(AppSchema):
    original_filename: str
    stored_filename: str
    relative_path: str
    content_type: str
    size_bytes: int
    width: int | None = None
    height: int | None = None


class UploadJob(AppSchema):
    job_id: str
    uploaded_at: datetime
    file_count: int
    files: list[UploadedImageInfo]
