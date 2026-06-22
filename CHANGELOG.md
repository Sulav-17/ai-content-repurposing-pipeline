# Changelog

## [1.0.0] - 2026-06-22

### Added

- Local-first FastAPI backend for transcript cleaning, deterministic analysis, structured content briefs, multi-platform content assets, Markdown export, saved history, media jobs, and health/readiness checks.
- Deterministic provider as the default generation path, with optional local Ollama support.
- Streamlit frontend for preview generation, saved-history workflows, media-job submission, status refresh, and Markdown downloads.
- PostgreSQL persistence through SQLAlchemy and Alembic.
- Redis/RQ media-job workflow using FFmpeg and whisper.cpp for local transcription.
- Docker Compose stack for API, frontend, PostgreSQL, Redis, migration service, and optional media worker.
- Deterministic evaluation harness with eight synthetic evaluation cases.

### Security

- Secrets and local environment files are ignored by Git.
- Model binaries are ignored by Git and must be supplied manually.
- Application containers run as a non-root user.
- Runtime hardening includes trusted-host configuration and basic security headers.
- Readiness and error responses avoid exposing credentials, URLs, SQL, stack traces, or subprocess output.

### Testing

- `.\.venv\Scripts\python.exe scripts\run_evaluation.py --output artifacts\evaluation-results.json` passed with 8 of 8 evaluation cases.
- `.\.venv\Scripts\python.exe -m pytest -q --basetemp <temporary-directory>` passed with 196 tests and 1 warning.
- Docker Compose configuration validation passed.
- Core Compose smoke testing passed.
- Media Compose smoke testing passed with a finished job at stage `complete` and progress `100`.
- CI runs the Python test suite, validates Compose configuration, builds Docker targets, starts the core stack, and runs the core smoke test.

### Documentation

- Added final architecture documentation, evaluation documentation, release notes, portfolio case study, resume bullets, demo script, screenshot checklist, launch content, and release checklist.
- Reorganized the README for portfolio review and local setup.

### Known Limitations

- The project is local-first and not deployed as a hosted production service.
- No authentication, multi-user ownership, publishing automation, cloud transcription, or paid AI provider integration is included.
- AI-assisted output still requires human review before publication.
- Media transcription requires local or containerized FFmpeg, whisper.cpp, Redis/RQ, and a manually supplied model.
