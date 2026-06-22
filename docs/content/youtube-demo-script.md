# YouTube Demo Package

## Title Options

1. Building a Local-First AI Content Repurposing Pipeline
2. FastAPI, Streamlit, Redis, PostgreSQL, and whisper.cpp in One Portfolio Project
3. Local AI Content Generation Without Paid APIs
4. End-to-End Content Repurposing with Deterministic Fallbacks
5. Dockerized FastAPI and Streamlit AI Workflow Demo

## Description

This walkthrough demonstrates a local-first AI Content Repurposing Pipeline built with FastAPI, Streamlit, PostgreSQL, Redis/RQ, FFmpeg, whisper.cpp, Docker Compose, and deterministic generation. The system turns transcripts or local media into structured content assets and Markdown exports, with optional local Ollama support.

No paid AI APIs, hosted deployment, or automatic model downloads are required.

## Chapter Outline

- 00:00 - Project problem
- 00:45 - Architecture overview
- 01:45 - Generate a deterministic preview
- 02:45 - Save and retrieve generation history
- 03:45 - Submit and track a media job
- 05:15 - Docker Compose and CI
- 06:15 - Evaluation and limitations

## Thumbnail Text Options

- Local AI Pipeline
- FastAPI + Streamlit
- No Paid APIs
- Transcript To Content

## 5-8 Minute Script

"In this video, I am walking through a local-first AI Content Repurposing Pipeline. The problem is simple: long-form source material often has to become platform-specific assets like YouTube descriptions, LinkedIn posts, short hooks, portfolio notes, and Markdown summaries.

The architecture starts with a Streamlit frontend. The frontend talks to FastAPI only through HTTP. FastAPI owns validation, transcript cleaning, deterministic analysis, content brief generation, platform asset generation, saved history, media jobs, and health checks.

The default provider is deterministic, so the project works without a model, without a paid API, and without network access. Optional Ollama support is local and explicit.

For text generation, I paste a transcript, choose the deterministic provider, and generate a preview. The response includes a content brief, five YouTube titles, a description, timestamped chapters when timestamps exist, a LinkedIn post, five short hooks, short-form concepts, portfolio notes, and Markdown export.

Saving is separate from preview generation. The stateless endpoint does not write to the database. The saved-generation endpoint reuses the same generation workflow, validates the response, stores it in PostgreSQL, and supports paginated history, full retrieval, and deletion.

The media workflow uses Redis and RQ. The API accepts an upload, stores it safely, and queues a job. The worker converts media with FFmpeg, transcribes with whisper.cpp, normalizes the transcript, and then reuses the exact same generation service. Model files are supplied manually and are not committed.

Docker Compose provides an optional reproducible runtime with PostgreSQL, Redis, migrations, FastAPI, Streamlit, and the optional media worker. Native Windows execution remains supported.

For release confidence, the repository includes automated tests, CI, Compose smoke tests, and a deterministic evaluation harness. The final local run passed 196 automated tests, and the evaluation harness passed 8 of 8 synthetic cases.

This is not a production SaaS product. It has no authentication, multi-user ownership, hosted deployment, or publishing automation. The focus is engineering: clean boundaries, deterministic fallback behavior, local AI integrations, persistence, background jobs, Docker packaging, and honest release documentation."
