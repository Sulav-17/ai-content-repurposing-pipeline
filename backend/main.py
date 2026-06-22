from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.content import router as content_router
from backend.api.routes.generation import router as generation_router
from backend.api.routes.generations import router as generations_router
from backend.api.routes.health import router as health_router
from backend.api.routes.media_jobs import router as media_jobs_router
from backend.api.routes.transcripts import router as transcripts_router
from backend.core.config import RuntimeSettings, get_runtime_settings
from backend.database.session import DatabaseConfigurationError, DatabaseUnavailableError
from backend.middleware.security_headers import add_security_headers
from backend.services.generation_history_service import GenerationNotFoundError


def create_app(runtime_settings: RuntimeSettings | None = None) -> FastAPI:
    settings = runtime_settings or get_runtime_settings()
    application = FastAPI(
        title="AI Content Repurposing Pipeline",
        version="0.1.0",
    )
    application.state.runtime_settings = settings

    if settings.trusted_hosts:
        application.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=list(settings.trusted_hosts),
        )
    if settings.security_headers_enabled:
        application.middleware("http")(add_security_headers)

    application.include_router(health_router)
    application.include_router(transcripts_router)
    application.include_router(analysis_router)
    application.include_router(content_router)
    application.include_router(generation_router)
    application.include_router(generations_router)
    application.include_router(media_jobs_router)

    _register_exception_handlers(application)
    return application


def _register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(
        DatabaseConfigurationError,
        handle_database_configuration_error,
    )
    application.add_exception_handler(
        DatabaseUnavailableError,
        handle_database_unavailable_error,
    )
    application.add_exception_handler(
        GenerationNotFoundError,
        handle_generation_not_found_error,
    )


def handle_database_configuration_error(
    request: Request,
    exc: DatabaseConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database configuration is missing."},
    )


def handle_database_unavailable_error(
    request: Request,
    exc: DatabaseUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is unavailable."},
    )


def handle_generation_not_found_error(
    request: Request,
    exc: GenerationNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Generation was not found."},
    )

app = create_app()
