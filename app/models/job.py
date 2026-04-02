"""将来の DB 導入を見据えたジョブモデル。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class JobRecord:
    """永続化導入前の簡易ジョブ表現。"""

    job_id: str
    created_at: datetime
    file_count: int
