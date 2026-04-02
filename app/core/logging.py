"""ロギング設定。"""

from __future__ import annotations

import logging

from app.core.constants import LOG_FORMAT


def configure_logging(level: str) -> None:
    """アプリ全体の基本ロギングを設定する。"""

    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=LOG_FORMAT)
