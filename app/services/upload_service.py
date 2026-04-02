"""アップロード全体のオーケストレーション。"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import UploadFile

from app.core.config import Settings
from app.core.exceptions import (
    CorruptedImageError,
    FileTooLargeError,
    TooManyFilesError,
    UnsupportedFileTypeError,
    ValidationError,
)
from app.schemas.result import UploadProcessOutcome
from app.schemas.upload import UploadedImageInfo, UploadJob
from app.services.dummy_analyzer import DummyAnalyzer
from app.services.file_service import FileService
from app.services.result_service import ResultService
from app.utils.filenames import extract_extension
from app.utils.ids import generate_job_id
from app.utils.image_checks import inspect_image
from app.utils.time import utc_now

logger = logging.getLogger(__name__)


class UploadService:
    """アップロードの検証、保存、解析をまとめて扱う。"""

    def __init__(
        self,
        *,
        settings: Settings,
        file_service: FileService,
        analyzer: DummyAnalyzer,
        result_service: ResultService,
    ) -> None:
        self.settings = settings
        self.file_service = file_service
        self.analyzer = analyzer
        self.result_service = result_service

    async def process_uploads(self, files: list[UploadFile] | None) -> UploadProcessOutcome:
        """複数画像のアップロード処理を実行する。"""

        upload_files = [file for file in files or [] if file.filename]
        if not upload_files:
            raise ValidationError("画像が選択されていません")
        if len(upload_files) > self.settings.max_upload_files:
            raise TooManyFilesError(
                f"アップロード上限を超えています。最大 {self.settings.max_upload_files} 件までです"
            )

        job_id = generate_job_id()
        logger.info("upload job started: job_id=%s count=%s", job_id, len(upload_files))
        saved_files = []

        try:
            for upload_file in upload_files:
                saved_files.append(await self._process_single_file(job_id, upload_file))

            job = UploadJob(
                job_id=job_id,
                uploaded_at=utc_now(),
                file_count=len(saved_files),
                files=saved_files,
            )
            analysis = self.analyzer.analyze(job)
            logger.info("dummy analyze completed: job_id=%s", job_id)
            return self.result_service.build_outcome(job=job, analysis=analysis)
        except Exception:
            self.file_service.delete_job_dir(job_id)
            raise

    async def _process_single_file(
        self,
        job_id: str,
        upload_file: UploadFile,
    ) -> UploadedImageInfo:
        original_filename = Path(upload_file.filename or "image").name
        content_type = upload_file.content_type or ""
        extension = extract_extension(original_filename)

        self._validate_extension(extension)
        self._validate_content_type(content_type)

        try:
            contents = await upload_file.read()
        finally:
            await upload_file.close()

        if not contents:
            raise CorruptedImageError("空の画像ファイルは受け付けられません")

        self._validate_size(len(contents))
        metadata = inspect_image(contents)

        return self.file_service.save_file(
            job_id=job_id,
            original_filename=original_filename,
            content_type=content_type,
            contents=contents,
            extension=extension,
            width=metadata.width,
            height=metadata.height,
        )

    def _validate_extension(self, extension: str) -> None:
        if extension not in self.settings.allowed_extensions:
            logger.warning("invalid extension: %s", extension)
            raise UnsupportedFileTypeError()

    def _validate_content_type(self, content_type: str) -> None:
        if content_type not in self.settings.allowed_content_types:
            logger.warning("invalid content type: %s", content_type)
            raise UnsupportedFileTypeError()

    def _validate_size(self, size_bytes: int) -> None:
        if size_bytes > self.settings.max_file_size_bytes:
            logger.warning("file too large: size_bytes=%s", size_bytes)
            raise FileTooLargeError(
                "画像サイズが上限を超えています。"
                f"1 ファイル {self.settings.max_file_size_mb} MB までです"
            )
