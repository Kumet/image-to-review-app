"""ファイル保存サービス。"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.core.exceptions import SaveFileError
from app.schemas.upload import UploadedImageInfo
from app.utils.filenames import build_stored_filename

logger = logging.getLogger(__name__)


class FileService:
    """ローカルファイル保存を担当する。"""

    def __init__(self, upload_root: Path) -> None:
        self.upload_root = upload_root

    def ensure_upload_root(self) -> None:
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        *,
        job_id: str,
        original_filename: str,
        content_type: str,
        contents: bytes,
        extension: str,
        width: int | None,
        height: int | None,
    ) -> UploadedImageInfo:
        """画像をローカルに保存し、メタ情報を返す。"""

        self.ensure_upload_root()
        job_dir = self.upload_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        stored_filename = build_stored_filename(extension)
        destination = job_dir / stored_filename

        try:
            destination.write_bytes(contents)
        except OSError as exc:
            logger.exception("failed to save file: job_id=%s path=%s", job_id, destination)
            raise SaveFileError() from exc

        relative_path = Path("uploads") / job_id / stored_filename
        logger.info("file saved: job_id=%s path=%s", job_id, relative_path)

        return UploadedImageInfo(
            original_filename=original_filename,
            stored_filename=stored_filename,
            relative_path=relative_path.as_posix(),
            content_type=content_type,
            size_bytes=len(contents),
            width=width,
            height=height,
        )

    def delete_job_dir(self, job_id: str) -> None:
        """失敗時に途中生成されたディレクトリを片付ける。"""

        job_dir = self.upload_root / job_id
        if not job_dir.exists():
            return
        try:
            shutil.rmtree(job_dir)
        except OSError:
            logger.warning("failed to cleanup upload directory: job_id=%s", job_id, exc_info=True)
