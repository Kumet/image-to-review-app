"""ファイル名関連ユーティリティ。"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from app.core.exceptions import UnsupportedFileTypeError


def extract_extension(filename: str) -> str:
    """ファイル名から正規化済み拡張子を返す。"""

    extension = Path(filename).suffix.lower()
    if not extension:
        raise UnsupportedFileTypeError()
    return extension


def build_stored_filename(extension: str) -> str:
    """保存用の UUID ベースファイル名を生成する。"""

    normalized = extension.lower().lstrip(".")
    return f"{uuid4().hex}.{normalized}"
