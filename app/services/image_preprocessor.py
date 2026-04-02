"""OCR 向け画像前処理サービス。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


class ImagePreprocessor:
    """OCR しやすい状態に画像を整える。"""

    def preprocess(
        self,
        image_path: Path,
        *,
        contrast: float = 1.8,
        threshold: int = 160,
        resize_scale: float = 2.0,
    ) -> Image.Image:
        with Image.open(image_path) as image:
            return self.preprocess_image(
                image,
                contrast=contrast,
                threshold=threshold,
                resize_scale=resize_scale,
            )

    def preprocess_image(
        self,
        image: Image.Image,
        *,
        contrast: float = 1.8,
        threshold: int = 160,
        resize_scale: float = 2.0,
    ) -> Image.Image:
        processed = image.convert("L")
        processed = ImageEnhance.Contrast(processed).enhance(contrast)
        processed = processed.filter(ImageFilter.SHARPEN)
        processed = processed.point(lambda pixel: 255 if pixel > threshold else 0)

        if resize_scale > 1.0:
            processed = processed.resize(
                (
                    max(1, int(processed.width * resize_scale)),
                    max(1, int(processed.height * resize_scale)),
                ),
                Image.Resampling.LANCZOS,
            )
        return processed
