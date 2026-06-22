# Short-Form Video Script

Target length: 30 to 45 seconds.

## Hook

"I built a local-first AI content pipeline that does not require paid AI APIs."

## Script

"Here is the workflow: paste a transcript or upload a local media file.

FastAPI validates the input, cleans the transcript, analyzes keywords and key points, and generates structured content assets.

The default provider is deterministic, so it works without a model. Optional Ollama stays local.

For media, Redis and RQ queue the job, FFmpeg converts the file, and whisper.cpp transcribes it. The same generation service then creates YouTube titles, descriptions, chapters, LinkedIn posts, short hooks, portfolio notes, and Markdown export.

The project also includes PostgreSQL history, Alembic migrations, Streamlit UI, Docker Compose, CI, 196 passing tests, and an eight-case deterministic evaluation harness.

Local-first, grounded, and portfolio-ready."
