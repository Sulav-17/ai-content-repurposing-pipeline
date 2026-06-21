from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.content import router as content_router
from backend.api.routes.generation import router as generation_router
from backend.api.routes.generations import router as generations_router
from backend.api.routes.transcripts import router as transcripts_router
from backend.database.session import DatabaseConfigurationError, DatabaseUnavailableError
from backend.services.generation_history_service import GenerationNotFoundError


app = FastAPI(
    title="AI Content Repurposing Pipeline",
    version="0.1.0",
)

app.include_router(transcripts_router)
app.include_router(analysis_router)
app.include_router(content_router)
app.include_router(generation_router)
app.include_router(generations_router)


@app.exception_handler(DatabaseConfigurationError)
def handle_database_configuration_error(
    request: Request,
    exc: DatabaseConfigurationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database configuration is missing."},
    )


@app.exception_handler(DatabaseUnavailableError)
def handle_database_unavailable_error(
    request: Request,
    exc: DatabaseUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is unavailable."},
    )


@app.exception_handler(GenerationNotFoundError)
def handle_generation_not_found_error(
    request: Request,
    exc: GenerationNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": "Generation was not found."},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-content-repurposing-pipeline",
    }
