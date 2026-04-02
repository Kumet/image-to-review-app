"""FastAPI アプリケーションエントリポイント。"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.routes import admin, health, pages, uploads
from app.services.dummy_analyzer import DummyAnalyzer
from app.services.extraction_field_service import ExtractionFieldService
from app.services.file_service import FileService
from app.services.result_service import ResultService
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """FastAPI アプリを生成する。"""

    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved_settings.upload_dir_path.mkdir(parents=True, exist_ok=True)
        app.state.extraction_field_service.ensure_config_file()
        yield

    app = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    templates = Jinja2Templates(directory=str(resolved_settings.templates_dir))
    templates.env.globals["app_name"] = resolved_settings.app_name

    file_service = FileService(resolved_settings.upload_dir_path)
    extraction_field_service = ExtractionFieldService(
        resolved_settings.extraction_config_file_path
    )
    result_service = ResultService()
    upload_service = UploadService(
        settings=resolved_settings,
        file_service=file_service,
        analyzer=DummyAnalyzer(extraction_field_service),
        result_service=result_service,
    )

    app.state.settings = resolved_settings
    app.state.templates = templates
    app.state.file_service = file_service
    app.state.extraction_field_service = extraction_field_service
    app.state.upload_service = upload_service

    app.mount("/static", StaticFiles(directory=str(resolved_settings.static_dir)), name="static")

    app.include_router(pages.router)
    app.include_router(admin.router)
    app.include_router(uploads.router)
    app.include_router(health.router)

    register_exception_handlers(app)
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """HTMX / 通常リクエスト向け例外レスポンスを登録する。"""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> Response:
        logger.warning("app error: %s", exc.user_message)
        return render_error_response(request, message=exc.user_message, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> Response:
        logger.exception("unexpected error", exc_info=exc)
        return render_error_response(request, message="画像の処理に失敗しました", status_code=500)


def render_error_response(request: Request, *, message: str, status_code: int) -> Response:
    """HTMX かどうかでエラーレスポンス形式を切り替える。"""

    if request.headers.get("HX-Request") == "true":
        templates = request.app.state.templates
        return templates.TemplateResponse(
            request=request,
            name="partials/error_message.html",
            context={"request": request, "message": message},
            status_code=status_code,
            headers={"HX-Retarget": "#error-area", "HX-Reswap": "innerHTML"},
        )
    return JSONResponse(status_code=status_code, content={"detail": message})


app = create_app()
