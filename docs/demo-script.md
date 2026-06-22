# Technical Demo Script

Target length: 4 to 6 minutes.

## 0:00-0:30 - Problem

Narration: "This project turns transcript, audio, or video source material into structured content assets while keeping the workflow local-first."

Screen action: Show the README and the Streamlit app title.

## 0:30-1:10 - Architecture

Narration: "The frontend is Streamlit over HTTP. FastAPI owns validation and workflows. The deterministic provider is always available. Optional Ollama, PostgreSQL, Redis/RQ, FFmpeg, and whisper.cpp are local integrations."

Screen action: Open `docs/architecture.md` and show the Mermaid diagram.

## 1:10-2:00 - Generate Preview

Narration: "A preview request calls `POST /content/generate` and does not save data."

Screen action: Paste a short transcript, choose `deterministic`, click Generate Preview, and show the structured result.

## 2:00-2:40 - Platform Assets And Markdown

Narration: "The response includes a brief, YouTube titles, description, chapters when timestamps exist, LinkedIn post, short hooks, concepts, portfolio notes, and Markdown export."

Screen action: Expand generated sections and download Markdown.

## 2:40-3:20 - Saved History

Narration: "Saving uses a separate endpoint so the preview workflow remains stateless."

Screen action: Click Generate and Save, switch to Saved History, open the saved record, and show confirmed deletion.

## 3:20-4:20 - Media Jobs

Narration: "Media uploads are queued with Redis/RQ. The worker converts with FFmpeg, transcribes with whisper.cpp, then reuses the same content-generation service."

Screen action: Submit a small local media file, refresh status, and show a completed job if services are running.

Fallback: If media services are not running, show the Media Jobs tab and explain the required local Redis, FFmpeg, whisper.cpp executable, and model.

## 4:20-5:10 - Docker And Verification

Narration: "Docker Compose provides a reproducible local stack. The normal test suite does not require Docker, Redis, PostgreSQL, Ollama, or a model."

Screen action: Show `docker compose ps`, `scripts/compose_smoke_test.py`, `scripts/compose_media_smoke_test.py`, and the pytest result.

## 5:10-6:00 - Close

Narration: "The project demonstrates local-first AI workflow design, validation boundaries, deterministic fallbacks, background media processing, persistence, Docker packaging, and release documentation."

Screen action: Show `docs/evaluation-results.md`, `docs/portfolio-case-study.md`, and `docs/release-checklist.md`.
