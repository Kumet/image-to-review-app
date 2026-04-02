"""アップロード処理用ルーター。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.post("/uploads", response_class=HTMLResponse)
async def upload_images(
    request: Request,
    images: Annotated[list[UploadFile] | None, File()] = None,
) -> HTMLResponse:
    """複数画像を受け取り、結果 partial を返す。"""

    templates = request.app.state.templates
    upload_service = request.app.state.upload_service
    outcome = await upload_service.process_uploads(images)

    return templates.TemplateResponse(
        request=request,
        name="partials/upload_result.html",
        context={
            "request": request,
            "settings": request.app.state.settings,
            "result": outcome.view,
        },
    )
