# Milestone 05 — Multi-Platform Content Generation and Markdown Export

## Goal

Build a local-first content-generation pipeline that transforms a validated transcript into structured platform-specific content assets and a reusable Markdown export.

This milestone combines:

* prompt chaining
* platform content generation
* structured output validation
* Markdown export

## Required Endpoint

```text
POST /content/generate
```

## Request Model

Create `ContentGenerationRequest`.

It must reuse existing transcript validation and contain:

* `text: str`
* `project_name: str`
* `provider: Literal["deterministic", "ollama"] = "deterministic"`

Requirements:

* transcript validation must not be duplicated
* project name must be nonblank after trimming
* project name must have a reasonable maximum length such as 120 characters
* unsupported providers return standard `422`

## Required Workflow

The generation service must:

1. receive validated transcript text
2. reuse existing cleaning and analysis
3. reuse the existing content-brief workflow
4. pass the brief and analysis into the selected content provider
5. generate platform-specific assets
6. validate assets with Pydantic
7. create Markdown using a separate deterministic export service
8. return the complete structured response

Do not duplicate transcript cleaning, analysis, or brief-generation logic.

## Required Schemas

### `YouTubeChapter`

* `timestamp: str`
* `title: str`

Both fields must be nonblank.

Timestamps must originate from the transcript. Providers must not fabricate timestamps.

### `PlatformContentAssets`

* `youtube_titles: list[str]`
* `youtube_description: str`
* `youtube_chapters: list[YouTubeChapter]`
* `linkedin_post: str`
* `short_hooks: list[str]`
* `short_form_concepts: list[str]`
* `portfolio_notes: list[str]`
* `project_summary: str`

Constraints:

* exactly 5 YouTube titles
* titles must be nonblank and unique
* YouTube description must be nonblank
* 0–12 chapters
* LinkedIn post must be nonblank
* exactly 5 short hooks
* hooks must be nonblank and unique
* 3–5 short-form concepts
* 3–8 portfolio notes
* project summary must be nonblank
* all string list items must be nonblank

### `ContentGenerationResponse`

* `provider: str`
* `project_name: str`
* `cleaned_text: str`
* `metadata: TranscriptMetadata`
* `analysis: TranscriptAnalysis`
* `brief: ContentBrief`
* `assets: PlatformContentAssets`
* `markdown_export: str`

Reuse existing transcript, analysis, and brief schemas.

## Deterministic Provider

The deterministic provider must:

* require no network
* require no model
* return stable output
* use existing keywords, key points, summary, and core message
* generate exactly five unique titles
* generate exactly five unique hooks
* avoid fabricated statistics, users, revenue, performance, or time savings
* avoid claiming technologies not present in source context
* only generate chapters from timestamps explicitly found in the cleaned transcript
* return no chapters when timestamps are unavailable
* generate portfolio notes as source-grounded notes rather than invented achievements

Identical input must produce identical output.

## Ollama Provider

The Ollama implementation must:

* remain optional
* use local `/api/generate`
* use `stream: false`
* read configuration from the existing config layer
* use `prompts/content_assets.txt`
* request JSON-only output
* parse the Ollama `response` field
* validate the result with `PlatformContentAssets`
* never execute generated code
* never fabricate timestamps when the transcript provides none

All Ollama HTTP behavior must be mocked in automated tests.

Provider error mapping must remain consistent:

* configuration, timeout, connection, unavailable provider → `503`
* malformed payload, invalid JSON, invalid schema → `502`

Do not silently fall back when Ollama was explicitly requested.

## Prompt Template

Create:

```text
prompts/content_assets.txt
```

The template must:

* request JSON only
* list every required field
* prohibit Markdown code fences
* require exactly five titles
* require exactly five hooks
* require 3–5 short-form concepts
* require 3–8 portfolio notes
* prohibit fabricated statistics and outcomes
* prohibit unsupported technical claims
* prohibit fabricated timestamps
* instruct the model to use only supplied transcript, analysis, and brief data

## Markdown Export

Create a pure deterministic export service.

It must generate Markdown with sections:

```text
# Project Name

## Project Summary
## Content Brief
## YouTube Titles
## YouTube Description
## YouTube Chapters
## LinkedIn Post
## Short-Form Hooks
## Short-Form Video Concepts
## Portfolio Notes
## Source Keywords
```

Requirements:

* use generated structured assets
* preserve multiline content
* use bullets or numbered lists appropriately
* omit the chapter list or state that no timestamped chapters were available
* perform no AI calls
* return identical Markdown for identical structured input

## Required Architecture

Create:

```text
backend/api/routes/generation.py
backend/schemas/generation.py
backend/services/content_generation_service.py
backend/services/markdown_export_service.py
prompts/content_assets.txt
```

The implementation may extend existing provider classes or create dedicated asset-provider classes.

Requirements:

* preserve `/content/brief`
* avoid duplicate provider-selection logic when practical
* providers must contain no FastAPI route logic
* export service must contain no provider or HTTP logic
* route must remain thin

## Tests

### Deterministic Generation

Test:

* valid schema
* stable repeated output
* exactly five unique titles
* exactly five unique hooks
* concept and portfolio-note limits
* empty chapters without source timestamps
* source timestamps preserved when present
* no obvious fabricated metrics
* sparse transcript handling

### Ollama Generation

Mock all HTTP calls.

Test:

* correct local request
* prompt contains structured context
* valid JSON parsing
* valid Pydantic result
* timeout and connection handling
* invalid JSON handling
* invalid schema handling
* fabricated timestamp rejection or prevention when no timestamps are provided

### Generation Service

Test:

* existing analysis and brief workflows are reused
* deterministic provider is default
* requested provider is selected
* generated assets are validated
* Markdown service is called
* complete response is returned

### Markdown Export

Test:

* every required section exists
* lists are correctly formatted
* multiline content is preserved
* empty chapters handled clearly
* deterministic repeated output

### Integration API

Test:

* default deterministic request returns `200`
* complete response structure
* exact title and hook counts
* Markdown export present
* project-name validation
* transcript validation
* invalid provider returns `422`
* mocked provider unavailable returns `503`
* mocked invalid provider output returns `502`
* existing endpoints remain functional

All previous tests must continue passing.

## Dependencies

No new dependency is expected.

Do not modify `requirements.txt` unless a genuine requirement conflict is identified before editing.

## Explicitly Excluded

Do not implement:

* OpenAI
* Claude
* paid APIs
* file uploads
* audio/video transcription
* database persistence
* history retrieval
* PostgreSQL
* Redis
* background jobs
* frontend
* Docker
* authentication
* social-media publishing
* automatic video clipping

## Acceptance Criteria

Milestone 5 is complete when:

1. `POST /content/generate` works locally.
2. Deterministic generation is the default.
3. Existing validation, cleaning, analysis, and brief generation are reused.
4. All assets pass Pydantic validation.
5. Exactly five titles and hooks are returned.
6. Chapters never fabricate timestamps.
7. Markdown export contains all required sections.
8. Deterministic requests produce identical responses.
9. Ollama remains optional and mocked in tests.
10. Existing endpoints and tests continue working.
11. No paid API is required.
12. The implementation is manually verified, committed, and pushed.
