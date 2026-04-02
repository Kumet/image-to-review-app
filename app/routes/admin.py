"""管理画面ルーター。"""

from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.schemas.admin import (
    ArticleTemplateCreate,
    ArticleTemplateUpdate,
    ExtractionFieldCreate,
    ExtractionFieldUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/extraction-fields", response_class=HTMLResponse)
async def extraction_field_list(request: Request) -> HTMLResponse:
    """抽出項目一覧画面を返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    fields = request.app.state.extraction_field_service.list_fields()
    return templates.TemplateResponse(
        request=request,
        name="pages/admin_extraction_fields.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "抽出項目管理",
            "fields": fields,
        },
    )


@router.get("/extraction-fields/new", response_class=HTMLResponse)
async def extraction_field_new_form(request: Request) -> HTMLResponse:
    """新規作成フォームを返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    return templates.TemplateResponse(
        request=request,
        name="pages/admin_extraction_field_form.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "抽出項目作成",
            "mode": "create",
            "field": None,
        },
    )


@router.post("/extraction-fields")
async def extraction_field_create(
    request: Request,
    key: str = Form(...),
    label: str = Form(...),
    field_type: str = Form(...),
    enabled: str | None = Form(default=None),
    required: str | None = Form(default=None),
    placeholder: str | None = Form(default=None),
    description: str | None = Form(default=None),
) -> RedirectResponse:
    """抽出項目を新規作成する。"""

    payload = ExtractionFieldCreate(
        key=key,
        label=label,
        field_type=field_type,
        enabled=enabled == "on",
        required=required == "on",
        placeholder=placeholder,
        description=description,
    )
    request.app.state.extraction_field_service.create_field(payload)
    return RedirectResponse(url="/admin/extraction-fields", status_code=303)


@router.get("/article-templates", response_class=HTMLResponse)
async def article_template_list(request: Request) -> HTMLResponse:
    """記事テンプレート一覧画面を返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    article_templates = request.app.state.article_template_service.list_templates()
    return templates.TemplateResponse(
        request=request,
        name="pages/admin_article_templates.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "記事テンプレート管理",
            "article_templates": article_templates,
        },
    )


@router.get("/article-templates/new", response_class=HTMLResponse)
async def article_template_new_form(request: Request) -> HTMLResponse:
    """記事テンプレート新規作成フォームを返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    variables = request.app.state.article_render_service.available_variables(
        [field.key for field in request.app.state.extraction_field_service.list_enabled_fields()]
    )
    return templates.TemplateResponse(
        request=request,
        name="pages/admin_article_template_form.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "記事テンプレート作成",
            "mode": "create",
            "article_template": None,
            "available_variables": variables,
        },
    )


@router.post("/article-templates")
async def article_template_create(
    request: Request,
    name: str = Form(...),
    description: str | None = Form(default=None),
    title_template: str = Form(...),
    body_template: str = Form(...),
    enabled: str | None = Form(default=None),
) -> RedirectResponse:
    """記事テンプレートを新規作成する。"""

    allowed_keys = {
        field.key for field in request.app.state.extraction_field_service.list_enabled_fields()
    }
    request.app.state.article_render_service.validate_template_strings(
        title_template=title_template,
        body_template=body_template,
        allowed_keys=allowed_keys,
    )
    request.app.state.article_template_service.create_template(
        ArticleTemplateCreate(
            name=name,
            description=description,
            title_template=title_template,
            body_template=body_template,
            enabled=enabled == "on",
        )
    )
    return RedirectResponse(url="/admin/article-templates", status_code=303)


@router.get("/article-templates/{template_id}/edit", response_class=HTMLResponse)
async def article_template_edit_form(request: Request, template_id: str) -> HTMLResponse:
    """記事テンプレート編集フォームを返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    article_template = request.app.state.article_template_service.get_template(template_id)
    variables = request.app.state.article_render_service.available_variables(
        [field.key for field in request.app.state.extraction_field_service.list_enabled_fields()]
    )
    return templates.TemplateResponse(
        request=request,
        name="pages/admin_article_template_form.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "記事テンプレート編集",
            "mode": "edit",
            "article_template": article_template,
            "available_variables": variables,
        },
    )


@router.post("/article-templates/{template_id}")
async def article_template_update(
    request: Request,
    template_id: str,
    name: str = Form(...),
    description: str | None = Form(default=None),
    title_template: str = Form(...),
    body_template: str = Form(...),
    enabled: str | None = Form(default=None),
) -> RedirectResponse:
    """記事テンプレートを更新する。"""

    allowed_keys = {
        field.key for field in request.app.state.extraction_field_service.list_enabled_fields()
    }
    request.app.state.article_render_service.validate_template_strings(
        title_template=title_template,
        body_template=body_template,
        allowed_keys=allowed_keys,
    )
    request.app.state.article_template_service.update_template(
        template_id,
        ArticleTemplateUpdate(
            name=name,
            description=description,
            title_template=title_template,
            body_template=body_template,
            enabled=enabled == "on",
        ),
    )
    return RedirectResponse(url="/admin/article-templates", status_code=303)


@router.post("/article-templates/{template_id}/toggle")
async def article_template_toggle(request: Request, template_id: str) -> RedirectResponse:
    """記事テンプレートの有効/無効を切り替える。"""

    request.app.state.article_template_service.toggle_template(template_id)
    return RedirectResponse(url="/admin/article-templates", status_code=303)


@router.post("/article-template-actions/reorder")
async def article_template_reorder(request: Request) -> RedirectResponse:
    """記事テンプレートの並び順を更新する。"""

    form = await request.form()
    template_ids = [
        template_id for template_id in form.getlist("template_ids") if isinstance(template_id, str)
    ]
    request.app.state.article_template_service.reorder_templates(template_ids)
    return RedirectResponse(url="/admin/article-templates", status_code=303)


@router.get("/extraction-fields/{field_id}/edit", response_class=HTMLResponse)
async def extraction_field_edit_form(request: Request, field_id: str) -> HTMLResponse:
    """編集フォームを返す。"""

    templates = request.app.state.templates
    settings = request.app.state.settings
    field = request.app.state.extraction_field_service.get_field(field_id)
    return templates.TemplateResponse(
        request=request,
        name="pages/admin_extraction_field_form.html",
        context={
            "request": request,
            "settings": settings,
            "page_title": "抽出項目編集",
            "mode": "edit",
            "field": field,
        },
    )


@router.post("/extraction-fields/{field_id}")
async def extraction_field_update(
    request: Request,
    field_id: str,
    label: str = Form(...),
    field_type: str = Form(...),
    enabled: str | None = Form(default=None),
    required: str | None = Form(default=None),
    placeholder: str | None = Form(default=None),
    description: str | None = Form(default=None),
) -> RedirectResponse:
    """抽出項目を更新する。"""

    payload = ExtractionFieldUpdate(
        label=label,
        field_type=field_type,
        enabled=enabled == "on",
        required=required == "on",
        placeholder=placeholder,
        description=description,
    )
    request.app.state.extraction_field_service.update_field(field_id, payload)
    return RedirectResponse(url="/admin/extraction-fields", status_code=303)


@router.post("/extraction-fields/{field_id}/toggle")
async def extraction_field_toggle(request: Request, field_id: str) -> RedirectResponse:
    """有効/無効を切り替える。"""

    request.app.state.extraction_field_service.toggle_field(field_id)
    return RedirectResponse(url="/admin/extraction-fields", status_code=303)


@router.post("/extraction-field-actions/reorder")
async def extraction_field_reorder(request: Request) -> RedirectResponse:
    """並び順を更新する。"""

    form = await request.form()
    field_ids = [field_id for field_id in form.getlist("field_ids") if isinstance(field_id, str)]
    request.app.state.extraction_field_service.reorder_fields(field_ids)
    return RedirectResponse(url="/admin/extraction-fields", status_code=303)
