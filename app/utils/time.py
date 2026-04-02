"""時刻ユーティリティ。"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """UTC 現在時刻を返す。"""

    return datetime.now(UTC)
