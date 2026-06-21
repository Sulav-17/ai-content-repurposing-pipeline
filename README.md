# AI Content Repurposing Pipeline

## Problem Statement

Content teams often start with long-form source material such as transcripts, audio, or video, then manually turn it into platform-specific content assets. This project will eventually support a local-first workflow for repurposing that source material into reusable content.

## Planned High-Level Solution

The planned system will provide a backend foundation for accepting source content, processing it through later milestone workflows, and producing structured outputs for different channels. Milestone 02 adds a deterministic transcript-cleaning boundary for pasted transcript text.

## Current Milestone Status

Milestone 02 is in progress. The current application exposes a local FastAPI backend with:

- `GET /health`
- `POST /transcripts/clean`

The transcript-cleaning endpoint accepts pasted transcript text through JSON, validates it, applies deterministic local cleaning rules, and returns cleaned text with metadata.

## Current Repository Structure

```text
ai-content-repurposing-pipeline/
|-- backend/
|   |-- api/
|   |   |-- __init__.py
|   |   `-- routes/
|   |       |-- __init__.py
|   |       `-- transcripts.py
|   |-- schemas/
|   |   |-- __init__.py
|   |   `-- transcript.py
|   |-- services/
|   |   |-- __init__.py
|   |   `-- transcript_service.py
|   |-- __init__.py
|   `-- main.py
|-- docs/
|   `-- milestones/
|       |-- milestone-01.md
|       `-- milestone-02.md
|-- tests/
|   |-- integration/
|   |   `-- test_transcript_api.py
|   |-- unit/
|   |   `-- test_transcript_service.py
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

## Transcript Cleaning Endpoint

Submit pasted transcript text as JSON:

```text
POST /transcripts/clean
```

Example request:

```json
{
  "text": "  [00:00] Host:\tHello   world.\r\n\r\nGuest:  Hi.  "
}
```

Example response:

```json
{
  "cleaned_text": "[00:00] Host: Hello world.\nGuest: Hi.",
  "metadata": {
    "original_character_count": 47,
    "cleaned_character_count": 37,
    "word_count": 6,
    "line_count": 2,
    "changed": true
  }
}
```

PowerShell example:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/transcripts/clean `
  -ContentType "application/json" `
  -Body '{"text":"  [00:00] Host:`tHello   world.`r`n`r`nGuest:  Hi.  "}'
```

### Validation Limits

- `text` is required.
- `text` must be a string.
- `text` must contain at least one character.
- `text` must contain at least one non-whitespace character.
- `text` must contain no more than 200,000 characters.
- Invalid requests return FastAPI's standard `422 Unprocessable Entity` response.

### Cleaning Rules

The cleaner applies these deterministic rules in order:

1. Normalize `\r\n` and `\r` to `\n`.
2. Replace tabs with spaces.
3. Strip leading and trailing whitespace from every line.
4. Collapse consecutive spaces within each line into one space.
5. Remove empty lines.
6. Join remaining lines using `\n`.

The cleaner preserves punctuation, capitalization, timestamps, speaker labels, line order, words, and sentence meaning. It does not summarize, paraphrase, correct grammar, call an AI model, write files, or use external services.

## Run Tests

```powershell
python -m pytest -q
```

## Current Limitations

- Transcript input is JSON-only pasted text.
- Transcript file uploads are not implemented.
- Audio and video uploads are not implemented.
- Transcription is not implemented.
- Content analysis and content generation are not implemented.
- No AI provider integration is implemented or required.
- No storage, database, background job system, frontend, Docker setup, authentication, deployment, or CI/CD is implemented.

Advanced infrastructure is intentionally deferred to future milestones.
