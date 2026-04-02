"""アプリケーション全体で使う定数。"""

from __future__ import annotations

DEFAULT_ALLOWED_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".webp")
DEFAULT_ALLOWED_CONTENT_TYPES: tuple[str, ...] = (
    "image/jpeg",
    "image/png",
    "image/webp",
)

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

DUMMY_LABELS: tuple[str, ...] = (
    "受理済み",
    "レビュー候補",
    "要確認",
    "サンプル解析",
)

DUMMY_COMMENTS: tuple[str, ...] = (
    "サンプル画像として受理しました。",
    "明るい印象のダミー結果です。",
    "画像サイズに基づく仮スコアを算出しました。",
    "将来の AI 解析へ差し替えやすい構造で返却しています。",
)
