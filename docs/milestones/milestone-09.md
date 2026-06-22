# Milestone 09 — Docker Compose, Production Hardening, CI, and End-to-End Testing

## Goal

Package and verify the AI Content Repurposing Pipeline as a reproducible multi-container application.

This milestone combines:

* Docker images
* Docker Compose orchestration
* PostgreSQL and Redis containers
* automatic Alembic migration execution
* FastAPI and Streamlit containers
* optional Linux RQ worker container
* FFmpeg and whisper.cpp worker tooling
* health and readiness endpoints
* safer runtime configuration
* non-root application containers
* GitHub Actions continuous integration
* automated Compose smoke testing
* optional media end-to-end testing

## Existing Behaviour To Preserve

Preserve:

* all existing API endpoints
* local Windows development
* local PostgreSQL support
* local WSL Redis support
* native Windows FFmpeg and whisper.cpp support
* deterministic generation
* optional Ollama
* saved history
* Streamlit workflows
* media jobs
* all existing tests

Docker must be an additional execution option, not a replacement for the current local workflow.

## New Health Endpoints

Preserve:

```text
GET /health
```

Add:

```text
GET /health/live
GET /health/ready
```

### Liveness

`GET /health/live` confirms only that the FastAPI process is running.

Return `200`:

```json
{
  "status": "alive",
  "service": "ai-content-repurposing-pipeline"
}
```

Do not connect to PostgreSQL or Redis from the liveness check.

### Readiness

`GET /health/ready` checks configured required dependencies.

Add settings:

```env
READINESS_REQUIRE_DATABASE=false
READINESS_REQUIRE_REDIS=false
```

The Docker environment will set both to `true`.

Readiness checks:

* PostgreSQL using a safe `SELECT 1`
* Redis using `PING`

Return `200` when required dependencies are ready.

Return `503` when a required dependency is:

* unconfigured
* unreachable
* unavailable

Use safe output such as:

```json
{
  "status": "not_ready",
  "checks": {
    "database": "unavailable",
    "redis": "ready"
  }
}
```

Never expose:

* database URLs
* Redis URLs
* credentials
* SQL statements
* exception messages
* stack traces

When a dependency is not required, report it as `skipped`.

## Runtime Hardening

Add configurable settings:

```env
APP_ENV=development
LOG_LEVEL=INFO
TRUSTED_HOSTS=localhost,127.0.0.1,testserver
SECURITY_HEADERS_ENABLED=true
```

Requirements:

* validate log-level values
* parse trusted hosts safely
* preserve `testserver` for FastAPI tests
* add trusted-host protection only when configured
* add safe security headers:

  * `X-Content-Type-Options: nosniff`
  * `X-Frame-Options: DENY`
  * `Referrer-Policy: no-referrer`
* do not expose sensitive configuration
* do not break local development
* do not add authentication or TLS termination

## Docker Images

Create one multi-stage `Dockerfile` with clearly named targets.

Recommended targets:

```text
python-base
api
frontend
whisper-builder
worker
```

Use:

```text
python:3.14-slim-bookworm
```

### Shared Python Base

Requirements:

* install Python dependencies before copying source when practical
* use `PYTHONDONTWRITEBYTECODE=1`
* use `PYTHONUNBUFFERED=1`
* set `/app` as working directory
* copy only required application files
* create a non-root application user
* ensure required writable directories belong to that user

### API Target

Run:

```text
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Do not use `--reload`.

### Frontend Target

Run:

```text
streamlit run frontend/app.py
```

Configure:

* address `0.0.0.0`
* port `8501`
* headless mode
* disabled usage-stat collection where supported

### Worker Target

The Linux worker image must:

* install FFmpeg
* build whisper.cpp from a pinned version in a builder stage
* copy only required whisper.cpp runtime artifacts into the worker image
* use the standard Linux RQ worker
* not use the Windows `SimpleWorker` workaround
* not download a Whisper model
* run as a non-root user

Use an argument such as:

```text
WHISPER_CPP_VERSION=v1.9.1
```

The model will be mounted at runtime.

## Docker Compose

Create:

```text
compose.yaml
```

Services:

### `postgres`

Use:

```text
postgres:18-alpine
```

Requirements:

* named persistent volume
* internal network
* health check using `pg_isready`
* credentials supplied through an untracked environment file
* do not expose PostgreSQL publicly by default

### `redis`

Use:

```text
redis:8-alpine
```

Requirements:

* named persistent volume
* health check using `redis-cli ping`
* internal network
* do not expose Redis publicly by default

### `migrate`

Requirements:

* use the API image
* depend on healthy PostgreSQL
* run:

```text
alembic upgrade head
```

* exit after successful migration
* do not restart indefinitely

### `api`

Requirements:

* depend on:

  * healthy PostgreSQL
  * healthy Redis
  * successful migration service
* expose port `8000`
* use Docker-internal database and Redis hostnames
* use the shared uploads volume
* health check `GET /health/ready`
* restart unless stopped
* run as non-root
* use `init: true`

### `frontend`

Requirements:

* depend on healthy API
* expose port `8501`
* use:

```text
API_BASE_URL=http://api:8000
```

* health check Streamlit’s health endpoint
* restart unless stopped
* run as non-root
* use `init: true`

### `worker`

Requirements:

* use profile:

```text
media
```

* depend on:

  * healthy PostgreSQL
  * healthy Redis
  * successful migration
* share the uploads volume with the API at the same container path
* mount:

```text
./models:/models:ro
```

* use:

```text
WHISPER_CPP_MODEL_PATH=/models/ggml-base.bin
```

* use Linux’s normal RQ worker
* restart unless stopped
* use `init: true`
* run as non-root

## Volumes

Create named volumes for:

* PostgreSQL data
* Redis data
* media uploads

The API and worker must mount the same media-upload volume at the same path.

## Networking

Use a private application network.

Only expose:

* FastAPI `8000`
* Streamlit `8501`

PostgreSQL and Redis must communicate through Docker service names and should not publish host ports by default.

## Docker Environment

Create:

```text
.env.docker.example
```

Include safe placeholders:

```env
POSTGRES_USER=ai_pipeline
POSTGRES_PASSWORD=replace-with-url-safe-password
POSTGRES_DB=ai_content_pipeline

APP_ENV=production
LOG_LEVEL=INFO
TRUSTED_HOSTS=localhost,127.0.0.1,api
SECURITY_HEADERS_ENABLED=true

READINESS_REQUIRE_DATABASE=true
READINESS_REQUIRE_REDIS=true

OLLAMA_BASE_URL=
OLLAMA_MODEL=
OLLAMA_TIMEOUT_SECONDS=60

MEDIA_MAX_UPLOAD_MB=200
MEDIA_JOB_TIMEOUT_SECONDS=3600
MEDIA_JOB_RESULT_TTL_SECONDS=86400
MEDIA_JOB_FAILURE_TTL_SECONDS=86400
WHISPER_CPP_THREADS=4
```

Requirements:

* `.env.docker` must be ignored by Git
* `.env.docker.example` must not contain real secrets
* use Docker service names in application connection strings
* document that special characters in URL passwords may require URL encoding
* fail clearly when required Compose variables are absent

## Whisper Model

Create:

```text
models/README.md
```

Document:

* model files are not committed
* place a compatible model at:

```text
models/ggml-base.bin
```

* model downloads are manual
* model licenses and storage requirements should be reviewed by the operator

Update `.gitignore` to exclude:

```text
models/*.bin
models/*.gguf
models/*.pt
```

Keep the README tracked.

## Docker Ignore

Create:

```text
.dockerignore
```

Exclude:

* `.git`
* `.venv`
* `.env`
* `.env.docker`
* `.pytest_cache`
* Python cache files
* local uploads
* model binaries
* screenshots and unnecessary generated files
* local PostgreSQL or Redis data
* test output

Do not exclude application source, migrations, prompts, frontend code, or required tests.

## Smoke Test

Create:

```text
scripts/compose_smoke_test.py
```

It must:

1. wait for the API readiness endpoint
2. confirm the API is ready
3. call deterministic `POST /content/generate`
4. validate the structured response
5. call `POST /generations`
6. save the generated ID
7. list history and confirm the record exists
8. retrieve the full saved record
9. delete the record
10. confirm the deleted record returns `404`
11. confirm the Streamlit health endpoint responds
12. exit nonzero on failure
13. never print secrets

Use bounded retries and timeouts.

## Optional Media Smoke Test

Create:

```text
scripts/compose_media_smoke_test.py
```

Requirements:

* accept a media-file path through a command-line argument
* submit a deterministic media job
* poll using bounded intervals and a total timeout
* require:

  * finished status
  * complete stage
  * progress 100
  * nonblank transcript
  * validated generation result
* optionally test saved persistence
* exit nonzero on failure
* display only safe status information

It must not be run by the normal automated test suite.

## Continuous Integration

Create:

```text
.github/workflows/ci.yml
```

Run on:

* pushes
* pull requests

Jobs should:

1. check out the repository
2. install a supported Python 3.14 runtime
3. install requirements
4. run the complete pytest suite
5. validate Compose configuration
6. build API and frontend images
7. build the media-worker image without downloading a model
8. start the core Compose stack
9. run the core Compose smoke test
10. always shut down the stack and remove CI volumes

CI must:

* use temporary non-secret test credentials
* never require Ollama
* never require a Whisper model for the core smoke test
* never publish images
* never deploy
* never expose secrets in logs

## Automated Tests

Add tests for:

### Health And Readiness

* liveness performs no dependency checks
* ready response with mocked healthy dependencies
* required database unavailable returns `503`
* required Redis unavailable returns `503`
* optional dependencies are skipped
* sensitive details are never returned
* existing `/health` remains unchanged

### Runtime Configuration

* valid and invalid log levels
* trusted-host parsing
* boolean readiness settings
* security-header toggle
* safe defaults

### Security Headers

* headers are present when enabled
* headers can be disabled
* existing endpoints still function

### Existing Workflows

Every existing test must continue passing.

The normal Python test suite must not require:

* Docker
* Docker Compose
* PostgreSQL
* Redis
* FFmpeg
* whisper.cpp
* a Whisper model
* Ollama
* internet access

Docker validation belongs in manual verification and CI.

## README

Document:

* native Windows execution
* Docker Desktop prerequisite
* creating `.env.docker`
* placing the Whisper model
* starting the core stack
* starting the media profile
* following logs
* checking service status
* running migrations
* running smoke tests
* stopping the stack
* removing volumes
* rebuilding images
* readiness and health endpoints
* differences between native Windows `SimpleWorker` and Linux container RQ worker
* troubleshooting

Commands should include:

```powershell
Copy-Item .env.docker.example .env.docker
docker compose --env-file .env.docker config
docker compose --env-file .env.docker up --build -d
python scripts/compose_smoke_test.py
docker compose --env-file .env.docker logs -f
docker compose --env-file .env.docker down
```

Full media profile:

```powershell
docker compose --env-file .env.docker --profile media up --build -d
```

Destructive reset:

```powershell
docker compose --env-file .env.docker down -v
```

Clearly explain that `down -v` permanently deletes containerized PostgreSQL and Redis data.

## Explicitly Excluded

Do not implement:

* cloud deployment
* Kubernetes
* Docker Swarm
* Terraform
* HTTPS certificates
* reverse proxy
* authentication
* multiple users
* image publishing
* container registry deployment
* monitoring platforms
* Prometheus
* Grafana
* cloud databases
* cloud transcription
* paid APIs
* automatic model downloads

## Acceptance Criteria

Milestone 9 is complete when:

1. Docker images build successfully.
2. The core Compose stack starts with one command.
3. PostgreSQL and Redis use health checks.
4. Alembic runs before the API starts.
5. FastAPI readiness checks required dependencies.
6. Streamlit communicates with the API through the Compose network.
7. The media worker is available through the `media` profile.
8. API and worker share uploads safely.
9. The model is mounted and never committed.
10. Application containers run as non-root.
11. Existing local Windows workflows still work.
12. Core Compose smoke testing passes.
13. Optional media Compose smoke testing passes when a model is mounted.
14. GitHub Actions runs tests, builds containers, and performs core smoke testing.
15. No deployment, authentication, paid API, or future milestone work is added.
16. The implementation is manually verified, committed, and pushed.
