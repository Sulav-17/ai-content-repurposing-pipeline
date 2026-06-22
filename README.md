# AI Content Repurposing Pipeline

Local-first FastAPI and Streamlit pipeline for turning transcripts or local media files into structured content assets, Markdown exports, and optional saved generation history.

## Demo And Screenshots

Screenshots are not committed or fabricated. Use the capture checklist in [docs/screenshots/README.md](docs/screenshots/README.md) and the demo walkthrough in [docs/demo-script.md](docs/demo-script.md).

## Key Capabilities

- Validate and clean pasted transcript text.
- Analyze transcripts with deterministic keyword and key-point extraction.
- Generate structured content briefs.
- Generate YouTube titles, YouTube descriptions, timestamped chapters, LinkedIn posts, short hooks, short-form concepts, portfolio notes, project summaries, and Markdown exports.
- Use deterministic generation by default with no model, network, or paid API.
- Optionally use a local Ollama model when explicitly configured.
- Save generated results to PostgreSQL only when requested.
- Browse, open, download, and delete saved generations.
- Upload local audio/video for asynchronous transcription and generation.
- Run natively on Windows or through Docker Compose.
- Run automated tests, deterministic evaluation, and Compose smoke checks.

## Architecture

The frontend is Streamlit over HTTP. FastAPI owns validation and workflows. Service modules handle cleaning, analysis, brief generation, platform asset generation, Markdown export, persistence, and media jobs. Providers contain no FastAPI route logic.

See [docs/architecture.md](docs/architecture.md).

```mermaid
flowchart LR
    frontend["Streamlit"] --> api["FastAPI"]
    api --> services["Generation services"]
    services --> providers["Provider layer"]
    providers --> deterministic["Deterministic"]
    providers --> ollama["Optional local Ollama"]
    api --> postgres["PostgreSQL"]
    api --> redis["Redis"]
    redis --> worker["RQ worker"]
    worker --> ffmpeg["FFmpeg"]
    worker --> whisper["whisper.cpp"]
    worker --> services
```

## Technology Stack

- Python 3.14
- FastAPI, Pydantic, Uvicorn
- Streamlit
- PostgreSQL, SQLAlchemy, Alembic
- Redis, RQ
- FFmpeg, whisper.cpp
- Docker Compose
- httpx, pytest
- GitHub Actions

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Start FastAPI:

```powershell
python -m uvicorn backend.main:app --reload
```

Start Streamlit in another terminal:

```powershell
python -m streamlit run frontend/app.py
```

Open:

```text
http://127.0.0.1:8501
```

## Text Generation

Use the Streamlit Generate tab or call:

```text
POST /content/generate
```

Example:

```json
{
  "project_name": "Demo Project",
  "text": "[00:05] Host: Local generation keeps output grounded.",
  "provider": "deterministic"
}
```

The response includes cleaned transcript text, metadata, transcript analysis, content brief, platform assets, and Markdown export.

## Saved History

Persistent history requires PostgreSQL and a local `.env` value:

```env
DATABASE_URL=postgresql+psycopg://postgres:change-me@localhost:5432/ai_content_pipeline
```

Use your own local credentials and do not commit `.env`.

Run migrations:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
```

Saved-history endpoints:

- `POST /generations`
- `GET /generations?limit=20&offset=0`
- `GET /generations/{generation_id}`
- `DELETE /generations/{generation_id}`

`POST /content/generate` remains stateless. Records are saved only through `POST /generations` or media jobs with saving enabled.

## Media Workflow

Media jobs require Redis, FFmpeg, whisper.cpp, and a local whisper.cpp model. The application does not download models automatically.

Configure `.env`:

```env
REDIS_URL=redis://localhost:6379/0
RQ_QUEUE_NAME=media-processing
MEDIA_UPLOAD_DIR=.data/uploads
MEDIA_MAX_UPLOAD_MB=200
MEDIA_JOB_TIMEOUT_SECONDS=3600
MEDIA_JOB_RESULT_TTL_SECONDS=86400
MEDIA_JOB_FAILURE_TTL_SECONDS=86400
FFMPEG_EXECUTABLE=ffmpeg
WHISPER_CPP_EXECUTABLE=
WHISPER_CPP_MODEL_PATH=
WHISPER_CPP_THREADS=4
```

Media endpoints:

- `POST /media-jobs`
- `GET /media-jobs/{job_id}`
- `DELETE /media-jobs/{job_id}`

The worker converts media with FFmpeg, transcribes with whisper.cpp, then reuses the existing content-generation service. Temporary files are cleaned on success and failure paths.

## Native Windows Setup

Run FastAPI and Streamlit in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
.\.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

Run a Windows-compatible RQ worker:

```powershell
rq worker -w rq.worker.SimpleWorker --url redis://127.0.0.1:6379/0 media-processing
```

`SimpleWorker` is a local Windows compatibility choice. It provides less process isolation and heartbeat behavior than the normal worker model. The installed RQ `SpawnWorker` path encountered an `os.wait4` incompatibility on Windows. Do not treat `SimpleWorker` as the preferred production worker.

## Docker Setup

Docker is an additional local runtime path, not a replacement for native Windows execution.

Create a Docker environment file:

```powershell
Copy-Item .env.docker.example .env.docker
```

Edit `.env.docker` with URL-safe local credentials. Do not commit it.

Validate Compose:

```powershell
docker compose --env-file .env.docker config
```

Start the core stack:

```powershell
docker compose --env-file .env.docker up --build -d
```

Run the core smoke test:

```powershell
.\.venv\Scripts\python.exe scripts\compose_smoke_test.py
```

Start the optional media profile:

```powershell
docker compose --env-file .env.docker --profile media up --build -d
```

Linux containers use the normal RQ worker:

```text
rq worker media-processing --url redis://redis:6379/0
```

Place a compatible model at:

```text
models/ggml-base.bin
```

Model binaries are ignored by Git. Review model licensing and storage requirements before adding one.

Run the optional media smoke test:

```powershell
.\.venv\Scripts\python.exe scripts\compose_media_smoke_test.py path\to\sample.wav
```

Stop the stack without deleting volumes:

```powershell
docker compose --env-file .env.docker --profile media down
```

Destructive reset:

```powershell
docker compose --env-file .env.docker down -v
```

`down -v` permanently deletes containerized PostgreSQL and Redis data.

## Ollama Option

Ollama is optional and local. The deterministic provider is the default.

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=
OLLAMA_TIMEOUT_SECONDS=60
```

If `provider` is `ollama`, the API calls local Ollama and validates the structured response. It does not silently fall back to deterministic output.

## Testing And Evaluation

Run the deterministic evaluation:

```powershell
.\.venv\Scripts\python.exe scripts\run_evaluation.py --output artifacts\evaluation-results.json
```

Latest local result:

- 8 of 8 evaluation cases passed.

Run the complete test suite with a unique temp directory:

```powershell
$testTemp = Join-Path $env:TEMP ("ai-content-pipeline-m10-" + [guid]::NewGuid())
.\.venv\Scripts\python.exe -m pytest -q --basetemp $testTemp
Remove-Item -Recurse -Force $testTemp -ErrorAction SilentlyContinue
```

Latest local result:

- 196 passed, 1 warning.

Latest Docker verification:

- Docker Compose configuration passed.
- Core Compose smoke test passed.
- Media Compose smoke test passed with a finished job at `complete` / `100`.

See [docs/evaluation.md](docs/evaluation.md) and [docs/evaluation-results.md](docs/evaluation-results.md).

## API Endpoints

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `POST /transcripts/clean`
- `POST /transcripts/analyze`
- `POST /content/brief`
- `POST /content/generate`
- `POST /generations`
- `GET /generations`
- `GET /generations/{generation_id}`
- `DELETE /generations/{generation_id}`
- `POST /media-jobs`
- `GET /media-jobs/{job_id}`
- `DELETE /media-jobs/{job_id}`

## Project Structure

```text
backend/      FastAPI routes, schemas, services, providers, database, jobs
frontend/     Streamlit app, HTTP API client, renderers
prompts/      Local prompt templates for optional Ollama
migrations/   Alembic environment and database migration
scripts/      Evaluation and Compose smoke-test scripts
tests/        Unit, integration, and evaluation tests
docs/         Architecture, evaluation, release, demo, and portfolio docs
models/       README plus ignored local model binaries
```

## Security And Safety

- `.env`, `.env.docker`, generated artifacts, upload data, and model binaries are ignored.
- `.env.example` and `.env.docker.example` contain placeholders only.
- The application does not commit model files.
- The deterministic provider requires no network or paid API.
- Provider output is validated with Pydantic.
- Readiness and error responses avoid exposing credentials, URLs, SQL, tracebacks, or subprocess output.
- Containers run as a non-root user.

## Limitations

- No authentication or multi-user ownership.
- No hosted deployment is included.
- No production usage is claimed.
- No social-media publishing automation.
- No automatic video clipping.
- No automatic Whisper model downloads.
- No OpenAI, Claude, cloud transcription, or paid API integration.
- Ollama output quality depends on the local model and still needs review.
- Generated content is not guaranteed to be accurate or publication-ready.
- The deterministic analyzer is intentionally simple and does not understand full semantics.

## Portfolio Case Study

See [docs/portfolio-case-study.md](docs/portfolio-case-study.md).

## Future Improvements

- Authentication and per-user saved history
- Search and filtering for history
- Richer local evaluation cases
- Subtitle and caption export
- More local provider adapters
- Optional deployment documentation

## License Status

No software license has been added.

## Release Materials

- [CHANGELOG.md](CHANGELOG.md)
- [docs/releases/v1.0.0.md](docs/releases/v1.0.0.md)
- [docs/release-checklist.md](docs/release-checklist.md)
- [docs/resume-bullets.md](docs/resume-bullets.md)
- [docs/content/youtube-demo-script.md](docs/content/youtube-demo-script.md)
- [docs/content/linkedin-launch-post.md](docs/content/linkedin-launch-post.md)
- [docs/content/short-form-video-script.md](docs/content/short-form-video-script.md)
