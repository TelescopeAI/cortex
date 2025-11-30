import logging
import os
import time
from contextlib import asynccontextmanager

import uvicorn
from Secweb import SecWeb
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from cortex.__version__ import version
from cortex.api.docs.meta import DocsMeta
from cortex.api.routers import PUBLIC_ROUTES
from cortex.core.config.execution_env import ExecutionEnv
from cortex.core.onboarding.onboard import OnboardingManager
from fastapi.logger import logger as fastapi_logger

API_PREFIX = "/api"
AUTH_PREFIX = "/auth"
API_VERSION_PREFIX = "/v1"
API_URL_PREFIX = API_PREFIX + API_VERSION_PREFIX
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 9002
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).split(API_PREFIX)[0]
print(ROOT_DIR)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")



if ExecutionEnv.https_enabled():
    SSL_KEYFILE = os.getenv("LOCAL_SSL_KEY")
    SSL_CERTIFICATE = os.getenv("LOCAL_SSL_CERT")

ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:9002").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events, including database migrations on startup."""
    # Startup: Execute before the application starts receiving requests
    logger = logging.getLogger(__name__)
    logger.info("Starting Cortex API server...")
    
    # Run onboarding operations
    try:
        onboarding_manager = OnboardingManager()
        success = onboarding_manager.run()
        if not success:
            logger.error("Onboarding operations failed. Please check your configuration.")
            # Note: We don't exit here to allow the application to start for debugging
    except Exception as e:
        logger.error(f"Error during onboarding operations: {e}")
        # Note: We don't exit here to allow the application to start for debugging
    
    yield
    
    # Shutdown: Execute after the application finishes handling requests
    logger.info("Shutting down Cortex API server...")


app = FastAPI(
    title="Cortex Semantic API",
    version=version,
    description=DocsMeta.API_GLOBAL_DESCRIPTION,
    docs_url=None,
    redoc_url=None,
    openapi_url=API_URL_PREFIX + "/openapi.json",
    openapi_tags=DocsMeta.TAGS_META,
    contact={"name": "Telescope Team", "url": "https://jointelescope.com",
             "email": "info@jointelescope.com"},
    lifespan=lifespan
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# FastAPIInstrumentor.instrument_app(app)
if not ExecutionEnv.is_local():
    SecWeb(app=app, Option={'coep': {'Cross-Origin-Embedder-Policy': 'require-corp'},
                            'coop': {'Cross-Origin-Opener-Policy': 'same-origin'},
                            'xss': {'X-XSS-Protection': '1; mode=block'},
                            'hsts': {'max-age': 31536000, 'includeSubDomains': True, 'preload': True}
                            })
    gunicorn_logger = logging.getLogger("gunicorn")
    log_level = gunicorn_logger.level

    root_logger = logging.getLogger()
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")

    # Use gunicorn error handlers for root, uvicorn, and fastapi loggers
    root_logger.handlers = gunicorn_error_logger.handlers
    uvicorn_access_logger.handlers = gunicorn_error_logger.handlers
    fastapi_logger.handlers = gunicorn_error_logger.handlers

    # Pass on logging levels for root, uvicorn, and fastapi loggers
    root_logger.setLevel(log_level)
    uvicorn_access_logger.setLevel(log_level)
    fastapi_logger.setLevel(log_level)



for route in PUBLIC_ROUTES:
    app.include_router(route["router"], prefix=API_URL_PREFIX)


@app.get('/', tags=["Health"])
def health():
    """Basic health check endpoint."""
    return {"status": "running"}


@app.get('/health', tags=["Health"])
def health_detailed():
    """Detailed health check endpoint including migration status."""
    from cortex.core.storage.migrations import get_migration_manager
    
    migration_manager = get_migration_manager()
    migration_status = migration_manager.get_migration_status()
    
    return {
        "status": "running",
        "migration_status": migration_status
    }


# @app.options("/{path:path}")
# async def options_handler():
#     return JSONResponse(content="OK", headers={
#         "Access-Control-Allow-Origin": "https://cortex.jointelescope.com",
#         "Access-Control-Allow-Credentials": "true",
#         "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
#         "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, Content-Type, Authorization, Accept,"
#                                         " Access-Control-Allow-Origin, Set-Cookie"
#     })


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["cache-control"] = "no-store"
    return response


# if ExecutionEnv.is_profiling_enabled():
#     @app.middleware("http")
#     async def add_sql_tap(request: Request, call_next):
#         profiler = sqltap.start()
#         response = await call_next(request)
#         statistics = profiler.collect()
#         sqltap.report(statistics, "qa/reports/result.html", report_format="html")
#         return response
#
#
#     app.add_middleware(
#         PyInstrumentProfilerMiddleware,
#         server_app=app,  # Required to output the profile on server shutdown
#         profiler_output_type="html",
#         is_print_each_request=False,  # Set to True to show request profile on
#                                       # stdout on each request
#         open_in_browser=True,  # Set to true to open your web-browser automatically
#                                # when the server shuts down
#         html_file_name="qa/reports/fastapi/profile.html"  # Filename for output
#     )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return PlainTextResponse(str(exc), status_code=400)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "HEAD", "OPTIONS", "DELETE"],
    allow_headers=["Access-Control-Allow-Headers", 'Content-Type', 'Authorization', "Accept",
                   'Access-Control-Allow-Origin', "Set-Cookie"]
)

reload_dirs = [os.path.join(ROOT_DIR, "api"), os.path.join(ROOT_DIR, "core")]


def start_api_server():
    if ExecutionEnv.https_enabled():
        uvicorn.run("cortex.api.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True, reload_dirs=reload_dirs,
                    ssl_keyfile=SSL_KEYFILE, ssl_certfile=SSL_CERTIFICATE, server_header=False)
    else:
        uvicorn.run("cortex.api.main:app", host=SERVER_HOST, port=SERVER_PORT, reload=True, reload_dirs=reload_dirs,
                    server_header=False)


if __name__ == "__main__":
    start_api_server()
