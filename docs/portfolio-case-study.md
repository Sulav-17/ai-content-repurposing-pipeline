# Portfolio Case Study

## 1. Project Overview

AI Content Repurposing Pipeline is a local-first FastAPI and Streamlit application that turns transcripts or local media files into structured content assets, Markdown exports, and optionally saved generation history.

## 2. Problem

Long-form source material often needs to become YouTube descriptions, LinkedIn posts, short hooks, portfolio notes, and summaries. Manually reformatting the same source across channels is repetitive and error-prone.

## 3. Goals

- Keep the workflow local-first.
- Provide deterministic generation by default.
- Support optional local Ollama without requiring it.
- Store generated results only when explicitly requested.
- Add asynchronous media transcription without paid APIs.
- Package the system with Docker Compose while preserving native Windows execution.

## 4. Constraints

The project avoids OpenAI, Claude, paid APIs, automatic model downloads, deployment claims, authentication, multi-user support, and fabricated performance or business metrics.

## 5. Architecture

The system uses a FastAPI backend, Streamlit frontend, deterministic and optional Ollama providers, PostgreSQL persistence, Redis/RQ jobs, FFmpeg conversion, whisper.cpp transcription, Alembic migrations, and Docker Compose orchestration.

## 6. User Workflows

- Generate a preview from pasted transcript text.
- Generate and save a result to PostgreSQL.
- Browse, open, download, and delete saved records.
- Upload local media, track a background job, view transcription, generate content, and optionally save it.

## 7. Technologies

FastAPI, Pydantic, Streamlit, SQLAlchemy, Alembic, PostgreSQL, Redis, RQ, FFmpeg, whisper.cpp, Docker Compose, GitHub Actions, httpx, pytest, and Python 3.14.

## 8. Engineering Decisions

The backend keeps routes thin and moves logic into services and providers. Pydantic validates request and provider output. Docker is additive rather than a replacement for native workflows.

## 9. Local-First AI Strategy

Deterministic generation is always available without a model or network. Ollama is optional, local, and explicitly requested. Media transcription uses local whisper.cpp and a manually supplied model.

## 10. Data Validation And Safety

Transcript validation rejects blank and oversized input. Generated assets are schema-validated. Timestamped chapters are restricted to source timestamps. The evaluation harness checks configured unsupported claims without rejecting source-supported numbers.

## 11. Persistence Design

`POST /content/generate` remains stateless. `POST /generations` reuses the same generation service and persists the full validated output. History lists omit transcript and Markdown until a full record is requested.

## 12. Asynchronous Media Workflow

Media uploads are saved with generated filenames. RQ jobs convert media with FFmpeg, transcribe with whisper.cpp, generate content through the existing pipeline, optionally save results, update safe job status, and clean temporary files.

## 13. Testing Strategy

The final local run reported 196 passing automated tests and 1 warning. Tests cover services, providers, API routes, database behavior, migrations, frontend helpers, media jobs, health/readiness, and the evaluation harness.

## 14. Docker And CI

Docker Compose defines PostgreSQL, Redis, migration, API, frontend, and optional worker services. GitHub Actions runs pytest, validates Compose, builds images, starts the core stack, and runs the core smoke test.

## 15. Challenges And Solutions

- Grounding generated chapters: normalize and whitelist source timestamps.
- Optional local model behavior: validate Ollama output and never silently fall back.
- Windows media workers: document `SimpleWorker` as a compatibility choice and use the normal worker model in Linux containers.
- Release confidence: add deterministic evaluation cases and smoke tests without external services in the normal pytest suite.

## 16. Results

Verified evidence currently includes an 8 of 8 deterministic evaluation pass, a 196-test pytest pass, Docker Compose configuration validation, a passing core Compose smoke test, and a passing media Compose smoke test. These are local verification results, not hosted production metrics.

## 17. Limitations

The project is local-only, unauthenticated, and not multi-user. Generated content still needs human review. Media jobs require Redis, FFmpeg, whisper.cpp, and a local model. No public deployment, customer adoption, revenue, or performance improvement is claimed.

## 18. Future Improvements

- Authentication and user ownership
- Search and filtering for saved history
- Richer evaluation cases
- Subtitle export
- Optional deployment documentation
- Additional local provider adapters

## 19. Repository And Demo References

See `README.md`, `docs/architecture.md`, `docs/evaluation.md`, `docs/demo-script.md`, and `docs/screenshots/README.md`.
