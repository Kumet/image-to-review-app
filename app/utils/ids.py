"""ID 生成ユーティリティ。"""

from __future__ import annotations

from uuid import uuid4


def generate_job_id() -> str:
    """ジョブ単位の一意 ID を返す。"""

    return uuid4().hex
