"""ヘルスチェック用ルーター。"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """簡易ヘルスチェックを返す。"""

    return {"status": "ok"}
