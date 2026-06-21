from fastapi import FastAPI

from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.content import router as content_router
from backend.api.routes.transcripts import router as transcripts_router


app = FastAPI(
    title="AI Content Repurposing Pipeline",
    version="0.1.0",
)

app.include_router(transcripts_router)
app.include_router(analysis_router)
app.include_router(content_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-content-repurposing-pipeline",
    }
