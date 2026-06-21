# Milestone 04 — Local Structured Content Brief Generation

## Goal

Create a local-first structured content brief workflow using a provider abstraction.

The application must work without a paid API. A deterministic provider must be the default. An optional Ollama provider may generate the same structured brief using a locally running model.

## Required Endpoint

```text
POST /content/brief
```

## Request

Create `ContentBriefRequest`.

It must reuse or inherit the existing transcript text validation and add:

```text
provider: "deterministic" | "ollama"
```

The default provider must be:

```text
deterministic
```

The accepted JSON should resemble:

```json
{
  "text": "Transcript text",
  "provider": "deterministic"
}
```

Missing, blank, whitespace-only, oversized, or invalid transcript text must preserve the existing `422` behavior.

Unsupported provider values must return `422`.

## Required Structured Brief

Create `ContentBrief` with:

* `summary: str`
* `core_message: str`
* `target_audience: str`
* `key_takeaways: list[str]`
* `suggested_tone: str`
* `source_keywords: list[str]`

Constraints:

* all string fields must be non-empty
* `key_takeaways` must contain between 1 and 5 values
* `source_keywords` must contain no more than 10 values
* empty strings must not be accepted
* generated data must be validated through Pydantic

Create `ContentBriefResponse` containing:

* `provider: str`
* `cleaned_text: str`
* `metadata: TranscriptMetadata`
* `analysis: TranscriptAnalysis`
* `brief: ContentBrief`

Reuse existing transcript and analysis schemas rather than duplicating them.

## Processing Workflow

The content brief service must:

1. receive validated transcript text
2. call the existing transcript analysis service
3. use its cleaned transcript, metadata, keywords, and key points
4. select the requested provider
5. generate a structured content brief
6. validate the provider result with `ContentBrief`
7. return a structured response

Do not duplicate transcript cleaning or analysis.

## Provider Interface

Create a provider protocol or abstract base with conceptually equivalent behavior:

```python
generate_brief(
    cleaned_text: str,
    keywords: list[str],
    key_points: list[str],
) -> ContentBrief
```

Provider implementations must not contain FastAPI route logic.

## Deterministic Provider

The deterministic provider must:

* require no network
* require no model
* use transcript keywords and key points
* produce stable output
* avoid unsupported claims
* avoid inventing statistics or business results
* use the first or strongest key points to construct the summary and core message
* use source keywords directly
* return identical output for identical input

A reasonable default target audience and tone may be used when the transcript does not clearly provide them.

Document these as deterministic defaults rather than inferred facts.

## Ollama Provider

The Ollama provider must:

* use local HTTP only
* use `httpx`
* read configuration from environment variables
* default base URL to:

```text
http://localhost:11434
```

* read the model name from `OLLAMA_MODEL`
* use `prompts/content_brief.txt`
* request JSON-only output
* parse the returned JSON
* validate it with `ContentBrief`
* never execute returned code

If Ollama is unavailable, times out, returns invalid JSON, or returns an invalid schema, the API must return a clear service error rather than crashing.

Use an appropriate FastAPI status code such as `503` for an unavailable local provider or `502` for an invalid provider response.

Do not silently claim Ollama succeeded when deterministic fallback was used.

## Configuration

Create `backend/core/config.py`.

Support:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=
OLLAMA_TIMEOUT_SECONDS=60
```

Update `.env.example` with placeholders only.

Do not place secrets in `.env.example`.

## Prompt Template

Create:

```text
prompts/content_brief.txt
```

The prompt must:

* request only valid JSON
* describe the exact required fields
* instruct the model to use only transcript-supported facts
* prohibit fabricated metrics, outcomes, or claims
* request 1–5 key takeaways
* request no more than 10 source keywords
* prohibit Markdown fences around the JSON

## Required Architecture

Create:

```text
backend/api/routes/content.py
backend/schemas/content.py
backend/services/content_brief_service.py
backend/providers/base.py
backend/providers/deterministic.py
backend/providers/ollama.py
backend/core/config.py
prompts/content_brief.txt
```

Modify:

```text
backend/main.py
README.md
.env.example
```

Do not modify `requirements.txt` unless a genuine missing dependency is found and explained before modification.

## Tests

### Deterministic Provider Tests

Test:

* stable output
* valid `ContentBrief`
* source keywords preserved
* maximum five takeaways
* no network usage
* sensible handling of one key point
* sensible handling of empty keyword results

### Ollama Provider Tests

Mock all HTTP calls.

Test:

* correct local request structure
* valid JSON response parsing
* Pydantic validation
* unavailable server handling
* timeout handling
* invalid JSON handling
* invalid schema handling

Do not require a real Ollama process during automated tests.

### Service Tests

Test:

* existing analysis service is reused
* requested provider is selected
* deterministic provider works
* Ollama provider may be injected or mocked
* invalid provider values cannot pass request validation

### Integration Tests

Test:

* deterministic request returns `200`
* response has the complete expected structure
* default provider is deterministic
* transcript cleaning occurs first
* analysis is included
* missing text returns `422`
* whitespace-only text returns `422`
* oversized text returns `422`
* invalid provider returns `422`
* mocked unavailable Ollama returns the documented service error

All previous tests must continue passing.

## Excluded

Do not implement:

* OpenAI
* Claude
* paid provider APIs
* YouTube titles
* descriptions
* LinkedIn posts
* short hooks
* portfolio notes
* database persistence
* file upload
* audio/video transcription
* Redis
* background jobs
* Docker
* frontend
* authentication

## Acceptance Criteria

Milestone 4 is complete when:

1. `POST /content/brief` works with the deterministic default.
2. Existing cleaning and analysis are reused.
3. The response is Pydantic validated.
4. Identical deterministic requests return identical results.
5. Ollama support is optional and local.
6. Ollama failures return clear errors.
7. Automated tests do not require a real model.
8. All existing tests pass.
9. No paid API is required.
10. README and `.env.example` are accurate.
11. No future milestone features are introduced.
12. The implementation is manually verified, committed, and pushed.
