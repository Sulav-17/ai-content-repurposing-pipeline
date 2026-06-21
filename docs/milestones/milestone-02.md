# Milestone 02 — Transcript Input, Validation, and Cleaning

## Status

Ready for implementation after Codex plan approval.

## Goal

Add a local, deterministic transcript-cleaning workflow exposed through FastAPI.

The API must accept pasted transcript text, validate the request, clean common formatting problems, and return the cleaned transcript with structured metadata.

## Business Context

The AI Content Repurposing Pipeline will eventually generate multiple content assets from transcripts, audio, and video.

Before analysis or generation can occur, transcript input must be valid and consistently formatted. This milestone creates that dependable input boundary without using an LLM, transcription provider, database, or paid API.

## Included Scope

* Pasted transcript input through JSON
* Pydantic request validation
* Pydantic response schemas
* Deterministic transcript cleaning
* Transcript metadata
* FastAPI transcript router
* Service-layer separation
* Unit tests
* API integration tests
* README documentation update

## Explicitly Excluded

Do not implement:

* Transcript file upload
* Audio upload
* Video upload
* Whisper or transcription
* Content analysis
* Key-point extraction
* Prompt templates
* OpenAI
* Claude
* Ollama
* Any paid API
* Content generation
* PostgreSQL
* SQLAlchemy
* Alembic
* Redis
* Celery
* RQ
* Background processing
* Streamlit
* Docker
* Authentication
* Deployment
* Future milestone folders unrelated to this milestone

## Required Endpoint

Create:

```text
POST /transcripts/clean
```

The endpoint must accept a JSON request body:

```json
{
  "text": "Transcript text"
}
```

## Request Validation

Create a Pydantic request model named:

```text
TranscriptCleanRequest
```

The `text` field must:

* be required
* be a string
* contain at least one non-whitespace character
* contain no more than 200,000 characters

Missing, blank, whitespace-only, oversized, or invalid input must produce FastAPI's standard `422 Unprocessable Entity` validation response.

Do not manually rewrite FastAPI's standard validation-error structure.

## Deterministic Cleaning Rules

Apply the following rules in this order:

1. Normalize `\r\n` and `\r` to `\n`.
2. Replace tabs with spaces.
3. Strip leading and trailing whitespace from every line.
4. Collapse consecutive spaces within each line into one space.
5. Remove empty lines.
6. Join remaining lines using `\n`.

The cleaner must preserve:

* line order
* capitalization
* punctuation
* timestamps
* speaker labels
* words and sentence meaning

The cleaner must not:

* summarize
* paraphrase
* correct grammar
* remove timestamps
* remove speaker labels
* call an AI model
* write files
* use external services

## Required Response

Create:

```text
TranscriptMetadata
TranscriptCleanResponse
```

The response must have this structure:

```json
{
  "cleaned_text": "Clean transcript",
  "metadata": {
    "original_character_count": 100,
    "cleaned_character_count": 80,
    "word_count": 14,
    "line_count": 3,
    "changed": true
  }
}
```

### Metadata Definitions

* `original_character_count`: `len()` of the original request text
* `cleaned_character_count`: `len()` of the final cleaned text
* `word_count`: number of whitespace-separated words in the cleaned text
* `line_count`: number of non-empty lines in the cleaned text
* `changed`: whether the cleaned text differs from the original text

## Required Architecture

Create:

```text
backend/api/__init__.py
backend/api/routes/__init__.py
backend/api/routes/transcripts.py
backend/schemas/__init__.py
backend/schemas/transcript.py
backend/services/__init__.py
backend/services/transcript_service.py
```

Responsibilities:

### `backend/schemas/transcript.py`

* request schema
* metadata schema
* response schema
* whitespace-only validation

### `backend/services/transcript_service.py`

* pure deterministic cleaning function
* metadata calculation
* no FastAPI route logic
* no external side effects

A small immutable dataclass may be used for the internal service result if it improves clarity.

### `backend/api/routes/transcripts.py`

* `APIRouter`
* `POST /transcripts/clean`
* request schema
* response model
* call to the transcript service
* mapping of service result to response schema

### `backend/main.py`

* preserve the existing FastAPI application
* preserve `GET /health`
* include the transcript router

## Dependencies

Add `pydantic` to `requirements.txt` because application code will import it directly.

Do not add any other dependency unless a genuine requirement cannot be met with Python's standard library and existing dependencies.

Use Python's standard `re` module for whitespace normalization.

## Tests

### Unit Tests

Create:

```text
tests/unit/test_transcript_service.py
```

Test:

1. repeated spaces are collapsed
2. tabs are normalized
3. blank lines are removed
4. Windows line endings are normalized
5. timestamps and speaker labels are preserved
6. metadata is calculated correctly
7. already-clean text reports `changed=False`

Tests may combine closely related behaviours when the assertions remain clear.

### Integration Tests

Create:

```text
tests/integration/test_transcript_api.py
```

Test:

1. valid request returns `200`
2. valid response has the exact expected content
3. whitespace-only input returns `422`
4. missing `text` returns `422`
5. oversized input returns `422`

The existing health test must continue to pass.

## README Changes

Update the README to include:

* Milestone 2 status
* transcript-cleaning feature
* endpoint method and path
* example JSON request
* example JSON response
* PowerShell request example
* validation limits
* cleaning rules
* test command
* current limitations
* statement that file uploads, AI generation, storage, and background jobs remain deferred

Do not claim future features are implemented.

## Commands

Run all tests:

```powershell
python -m pytest -q
```

If the Windows Python alias causes a failure:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run the API:

```powershell
python -m uvicorn backend.main:app --reload
```

Or:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

## Acceptance Criteria

Milestone 2 is accepted only when:

1. All required files exist.
2. Existing `/health` behaviour remains unchanged.
3. `POST /transcripts/clean` accepts valid JSON transcript input.
4. Missing input returns `422`.
5. Blank and whitespace-only input return `422`.
6. Input over 200,000 characters returns `422`.
7. Cleaning follows the required deterministic order.
8. Timestamps and speaker labels are preserved.
9. The response matches the required Pydantic schema.
10. Metadata values are correct.
11. Unit tests pass.
12. Integration tests pass.
13. Existing tests pass.
14. README instructions match the application.
15. No paid API or AI provider is required.
16. No future milestone technology is introduced.
17. Codex reports every changed file and command.
18. The user manually verifies the endpoint.
19. The user creates the Git commit.

## Definition of Done

Milestone 2 is complete when pasted transcript text can be validated and cleaned through the FastAPI endpoint, all required tests pass, existing functionality remains intact, documentation is accurate, and the completed work is committed and pushed by the user.
