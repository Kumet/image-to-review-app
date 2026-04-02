"""ID 生成ユーティリティ。"""

from __future__ import annotations

from uuid import uuid4


def generate_job_id() -> str:
    """ジョブ単位の一意 ID を返す。"""

    return uuid4().hex


def generate_field_id() -> str:
    """抽出項目単位の一意 ID を返す。"""

    return f"field_{uuid4().hex}"


def generate_template_id() -> str:
    """記事テンプレート単位の一意 ID を返す。"""

    return f"template_{uuid4().hex}"
