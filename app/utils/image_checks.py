"""Pillow を使った画像検証。"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.core.exceptions import CorruptedImageError


@dataclass(slots=True)
class ImageMetadata:
    width: int
    height: int


def inspect_image(contents: bytes) -> ImageMetadata:
    """画像として開けるか確認し、サイズを返す。"""

    try:
        with Image.open(BytesIO(contents)) as image:
            image.load()
            return ImageMetadata(width=image.width, height=image.height)
    except (UnidentifiedImageError, OSError) as exc:
        raise CorruptedImageError("画像の処理に失敗しました") from exc
