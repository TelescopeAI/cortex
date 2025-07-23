from fastapi import APIRouter, Depends, FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from scalar_fastapi import get_scalar_api_reference


def get_app() -> FastAPI:
    # Importing it here to prevent circular import
    from cortex.api.main import app
    return app


DocsRouter = APIRouter()

@DocsRouter.get("/docs", include_in_schema=False)
async def scalar_html(app: FastAPI = Depends(get_app)):
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )

@DocsRouter.get("/docs/classic", include_in_schema=False)
async def custom_swagger_ui_html(app: FastAPI = Depends(get_app)):
    print(app.openapi_url)
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@DocsRouter.get("/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@DocsRouter.get("/redoc", include_in_schema=False)
async def redoc_html(app: FastAPI = Depends(get_app)):
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )
