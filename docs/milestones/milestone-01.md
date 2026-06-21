# Milestone 01 — Repository Foundation and FastAPI Health Check

## Status

Ready for implementation after plan approval.

## Goal

Create the initial repository foundation for the AI Content Repurposing Pipeline and prove that a minimal FastAPI backend can run locally and pass an automated health-endpoint test.

## Business Context

The completed project will transform transcripts, audio, and video into reusable platform-specific content assets.

This milestone does not implement content processing. It establishes the backend application, repository standards, testing foundation, and development workflow required by later milestones.

## Included Scope

* Minimal Python repository structure
* FastAPI application
* `GET /health` endpoint
* JSON health response
* Basic automated API test
* Initial README
* `.gitignore`
* `.env.example`
* Direct dependency list
* Codex repository instructions
* Milestone documentation

## Explicitly Excluded

Do not implement or configure:

* Transcript submission
* Transcript files
* Transcript validation or cleaning
* Content analysis
* LLM integration
* Prompt templates
* Structured content-generation schemas
* OpenAI
* Claude
* Whisper or transcription providers
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis
* Celery
* RQ
* Background jobs
* Streamlit
* Docker
* Authentication
* Deployment
* CI/CD
* Advanced logging
* Future milestone folders that are not currently required

## Required Repository Structure

```text
ai-content-repurposing-pipeline/
├── backend/
│   ├── __init__.py
│   └── main.py
├── docs/
│   └── milestones/
│       └── milestone-01.md
├── tests/
│   └── test_health.py
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
└── requirements.txt
```

Do not create the complete future repository structure during this milestone.

## Application Requirements

Create a FastAPI application in `backend/main.py`.

The application must:

* expose an object named `app`
* have the title `AI Content Repurposing Pipeline`
* have version `0.1.0`
* expose `GET /health`
* return HTTP status code `200`
* return this exact JSON body:

```json
{
  "status": "ok",
  "service": "ai-content-repurposing-pipeline"
}
```

The health endpoint does not need a database, service class, dependency injection, or Pydantic response model during this milestone.

## Test Requirements

Create `tests/test_health.py`.

The test must:

* use `fastapi.testclient.TestClient`
* import `app` from `backend.main`
* send `GET /health`
* assert that the status code is `200`
* assert that the response JSON exactly matches the required body

Only one focused health-endpoint test is required.

## README Requirements

The initial README must contain:

* project name
* problem statement
* planned high-level solution
* current milestone status
* current repository structure
* prerequisites
* virtual-environment setup
* dependency installation
* local API command
* health-endpoint URL
* test command
* current limitations
* statement that advanced infrastructure is intentionally deferred

Do not claim that unimplemented features already exist.

## Environment File Requirements

Create `.env.example`.

It must not contain secrets.

It may document:

```text
APP_ENV=development
LOG_LEVEL=INFO
```

State in the file that these settings are placeholders and are not yet wired into the application.

## Dependencies

The direct dependencies for this milestone are:

```text
fastapi
uvicorn[standard]
httpx
pytest
python-dotenv
```

Do not add AI, database, task-queue, frontend, or Docker dependencies.

## Commands That Must Work

Run the application:

```powershell
python -m uvicorn backend.main:app --reload
```

Run the tests:

```powershell
python -m pytest -q
```

## Acceptance Criteria

Milestone 1 is accepted only when:

1. The required files exist.
2. The repository structure matches this specification.
3. The virtual environment is excluded from Git.
4. `.env` is excluded from Git.
5. No secret is committed.
6. The FastAPI application imports successfully.
7. The local server starts successfully.
8. `GET /health` returns HTTP `200`.
9. The JSON response exactly matches the required body.
10. The health test passes.
11. The README instructions match the actual commands.
12. No excluded future technology is introduced.
13. Codex summarizes every changed file.
14. The user manually verifies the endpoint and tests.
15. The user creates the Git commit.

## Definition of Done

Milestone 1 is complete when the health endpoint works locally, the automated test passes, the documentation is accurate, the repository has no unrelated changes, and the completed work is committed and pushed to GitHub.
