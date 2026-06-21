# AI Content Repurposing Pipeline

## Problem Statement

Content teams often start with long-form source material such as transcripts, audio, or video, then manually turn it into platform-specific content assets. This project will eventually support a local-first workflow for repurposing that source material into reusable content.

## Planned High-Level Solution

The planned system will provide a backend foundation for accepting source content, processing it through later milestone workflows, and producing structured outputs for different channels. Milestone 03 adds deterministic local transcript analysis for frequent keywords and verbatim key points.

## Current Milestone Status

Milestone 03 is in progress. The current application exposes a local FastAPI backend with:

- `GET /health`
- `POST /transcripts/clean`
- `POST /transcripts/analyze`

The transcript-cleaning endpoint accepts pasted transcript text through JSON, validates it, applies deterministic local cleaning rules, and returns cleaned text with metadata.

The transcript-analysis endpoint reuses the same request validation and cleaning service, then analyzes the cleaned transcript locally. It returns ranked keyword frequencies and up to five verbatim key-point sentences.

## Current Repository Structure

```text
ai-content-repurposing-pipeline/
|-- backend/
|   |-- api/
|   |   |-- __init__.py
|   |   `-- routes/
|   |       |-- analysis.py
|   |       |-- __init__.py
|   |       `-- transcripts.py
|   |-- schemas/
|   |   |-- analysis.py
|   |   |-- __init__.py
|   |   `-- transcript.py
|   |-- services/
|   |   |-- __init__.py
|   |   |-- content_analysis_service.py
|   |   `-- transcript_service.py
|   |-- __init__.py
|   `-- main.py
|-- docs/
|   `-- milestones/
|       |-- milestone-01.md
|       |-- milestone-02.md
|       `-- milestone-03.md
|-- tests/
|   |-- integration/
|   |   |-- test_analysis_api.py
|   |   `-- test_transcript_api.py
|   |-- unit/
|   |   |-- test_content_analysis_service.py
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

## Transcript Analysis Endpoint

Submit pasted transcript text as JSON:

```text
POST /transcripts/analyze
```

Example request:

```json
{
  "text": "  [00:00] Host:\tPython   API wins.\r\n\r\nGuest:  Python content works.  "
}
```

Example response:

```json
{
  "cleaned_text": "[00:00] Host: Python API wins.\nGuest: Python content works.",
  "metadata": {
    "original_character_count": 69,
    "cleaned_character_count": 59,
    "word_count": 9,
    "line_count": 2,
    "changed": true
  },
  "analysis": {
    "sentence_count": 2,
    "unique_word_count": 7,
    "top_keywords": [
      {
        "term": "python",
        "count": 2
      },
      {
        "term": "api",
        "count": 1
      },
      {
        "term": "content",
        "count": 1
      }
    ],
    "key_points": [
      "[00:00] Host: Python API wins.",
      "Guest: Python content works."
    ]
  }
}
```

PowerShell example:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/transcripts/analyze `
  -ContentType "application/json" `
  -Body '{"text":"  [00:00] Host:`tPython   API wins.`r`n`r`nGuest:  Python content works.  "}'
```

### Analysis Rules

The analyzer is deterministic and local-first:

1. Reuse the transcript request validation from the cleaning endpoint.
2. Clean the transcript with the existing cleaning service.
3. Split cleaned text into sentence candidates using `.`, `?`, `!`, and line boundaries.
4. Preserve punctuation, capitalization, timestamps, speaker labels, and sentence wording in key points.
5. Tokenize words with Python standard library regular expressions.
6. Ignore common English stop words, punctuation-only fragments, numeric-only tokens, and timestamp-only fragments.
7. Rank keywords by frequency descending, then alphabetically for ties.
8. Score sentences using normalized global token frequencies.
9. Remove exact duplicate key-point sentences while preserving the first occurrence.
10. Return at most ten keywords and at most five verbatim key points.

Keywords are frequent meaningful terms from the cleaned transcript. Key points are original transcript sentences selected by deterministic scoring; they are not summaries, paraphrases, or generated content.

## Run Tests

```powershell
python -m pytest -q
```

## Current Limitations

- Transcript input is JSON-only pasted text.
- Transcript file uploads are not implemented.
- Audio and video uploads are not implemented.
- Transcription is not implemented.
- Content generation is not implemented.
- The analyzer is intentionally simple and deterministic; it does not understand semantics, abbreviations, sentiment, or topics.
- No AI provider integration is implemented or required.
- No storage, database, background job system, frontend, Docker setup, authentication, deployment, or CI/CD is implemented.

Advanced infrastructure is intentionally deferred to future milestones.
AI generation remains deferred to a future milestone.
