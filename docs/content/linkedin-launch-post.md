# LinkedIn Launch Post

I finished a local-first AI Content Repurposing Pipeline as a portfolio project.

The goal: take transcript, audio, or video source material and turn it into structured content assets without depending on paid AI APIs.

What it includes:

- FastAPI backend
- Streamlit frontend
- deterministic generation by default
- optional local Ollama provider
- Pydantic validation for provider output
- PostgreSQL saved history with SQLAlchemy and Alembic
- Redis/RQ background media jobs
- FFmpeg conversion
- whisper.cpp transcription
- Docker Compose stack
- GitHub Actions CI
- deterministic evaluation harness

The system can generate content previews, save complete generation records, browse history, download Markdown exports, upload media, track background transcription jobs, and reuse the same generation service for transcript and media workflows.

The most important design constraint was keeping the project honest and local-first: no OpenAI, no Claude, no automatic model downloads, no fabricated metrics, and no claims that generated AI content is always accurate.

Final local evidence:

- 196 automated tests passed
- 8 of 8 deterministic evaluation cases passed

This is not a hosted product or a multi-user SaaS app. It is a focused engineering project showing backend architecture, provider boundaries, local AI workflows, persistence, async jobs, Docker packaging, and release documentation.
