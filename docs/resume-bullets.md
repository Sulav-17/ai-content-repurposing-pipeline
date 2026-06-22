# Resume Bullets

## Project Description

Built a local-first AI Content Repurposing Pipeline with FastAPI, Streamlit, PostgreSQL, Redis/RQ, FFmpeg, whisper.cpp, Docker Compose, deterministic generation, optional local Ollama support, and a 196-test automated suite.

## Standard Bullets

- Built a local-first FastAPI and Streamlit application that converts transcripts or local media into structured content assets, Markdown exports, and optional saved history.
- Implemented deterministic generation as the default path with optional local Ollama integration, validating every provider response through Pydantic schemas.
- Packaged the application with Docker Compose services for FastAPI, Streamlit, PostgreSQL, Redis, migrations, and an optional media worker.

## AI Engineering Bullets

- Designed a provider abstraction that supports deterministic generation and optional local Ollama without requiring paid APIs or network-based model providers.
- Added source-grounding rules for generated chapters by normalizing transcript timestamps and rejecting unsupported provider timestamps.
- Created an eight-case deterministic evaluation harness that checks schema validity, repeatability, grounding, required Markdown sections, and unsupported-claim guardrails.

## Backend Engineering Bullets

- Built FastAPI endpoints for transcript cleaning, analysis, content generation, saved generation history, media jobs, and health/readiness checks.
- Implemented PostgreSQL persistence with SQLAlchemy typed mappings, Alembic migrations, repository/service separation, and SQLite-based automated tests.
- Added Redis/RQ background processing for local media uploads, FFmpeg conversion, whisper.cpp transcription, safe status reporting, and temporary-file cleanup.

## Data And Automation Bullets

- Implemented deterministic transcript cleaning, keyword extraction, key-point selection, structured asset generation, and Markdown export using reusable service modules.
- Added CI coverage that runs pytest, validates Docker Compose, builds container targets, starts the core stack, and runs a core smoke test.
- Documented release-ready workflows, architecture, evaluation results, demo scripts, screenshot checklist, changelog, and v1.0.0 release notes without fabricated metrics.
