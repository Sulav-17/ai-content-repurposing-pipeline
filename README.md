# AI Content Repurposing Pipeline

## Problem Statement

Content teams often start with long-form source material such as transcripts, audio, or video, then manually turn it into platform-specific content assets. This project will eventually support a local-first workflow for repurposing that source material into reusable content.

## Planned High-Level Solution

The planned system will provide a backend foundation for accepting source content, processing it through later milestone workflows, and producing structured outputs for different channels. Milestone 01 only establishes the repository foundation and a minimal FastAPI health check.

## Current Milestone Status

Milestone 01 is in progress. The current application exposes a local FastAPI backend with a single `GET /health` endpoint and one automated API test.

## Current Repository Structure

```text
ai-content-repurposing-pipeline/
|-- backend/
|   |-- __init__.py
|   `-- main.py
|-- docs/
|   `-- milestones/
|       `-- milestone-01.md
|-- tests/
|   `-- test_health.py
|-- .env.example
|-- .gitignore
|-- AGENTS.md
|-- README.md
`-- requirements.txt
```

## Prerequisites

- Python 3.11 or newer
- PowerShell or another local terminal

## Virtual Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Dependency Installation

```powershell
python -m pip install -r requirements.txt
```

## Run the Local API

```powershell
python -m uvicorn backend.main:app --reload
```

## Health Endpoint

After the local API starts, open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "ai-content-repurposing-pipeline"
}
```

## Run Tests

```powershell
python -m pytest -q
```

## Current Limitations

- No transcript submission is implemented.
- No transcript validation, cleaning, or content analysis is implemented.
- No AI provider integration is implemented or required.
- No database, background job system, frontend, Docker setup, authentication, deployment, or CI/CD is implemented.

Advanced infrastructure is intentionally deferred to future milestones.
