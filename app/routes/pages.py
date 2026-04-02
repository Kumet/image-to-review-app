"""ページ系ルーター。"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """トップページを返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    return templates.TemplateResponse(
        request=request,
        name="pages/index.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "複数画像アップロード",
        },
    )
