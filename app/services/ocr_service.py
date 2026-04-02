"""OCR 実行サービス。"""

from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image
from pytesseract import TesseractError, TesseractNotFoundError

from app.schemas.result import OCRImageResult


class OCRService:
    """前処理済み画像からテキストを抽出する。"""

    def __init__(self, *, lang: str = "jpn+eng", config: str = "--psm 6") -> None:
        self.lang = lang
        self.config = config

    def extract_text(self, image: Image.Image, *, image_path: Path) -> OCRImageResult:
        try:
            raw_text = pytesseract.image_to_string(image, lang=self.lang, config=self.config)
        except (RuntimeError, TesseractError, TesseractNotFoundError):
            raw_text = ""

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        return OCRImageResult(image_path=str(image_path), raw_text=raw_text, lines=lines)
