# Milestone 03 — Deterministic Transcript Analysis and Key-Point Extraction

## Status

Ready for implementation after Codex plan approval.

## Goal

Add a deterministic, local transcript-analysis workflow that extracts frequent keywords and important original transcript sentences without using an LLM or external service.

## Business Context

The AI Content Repurposing Pipeline will later generate platform-specific content such as YouTube metadata, LinkedIn posts, short-form hooks, and portfolio notes.

Before generative AI is introduced, the application needs a dependable analysis stage that identifies meaningful transcript terms and strong source sentences. This stage provides reusable context, a free fallback, and testable behaviour.

## Included Scope

* Reuse existing transcript validation
* Reuse existing transcript cleaning
* Sentence detection
* Word tokenization
* English stop-word filtering
* Keyword frequency counting
* Deterministic keyword ranking
* Deterministic sentence scoring
* Up to five verbatim key points
* Structured Pydantic response models
* FastAPI analysis endpoint
* Unit tests
* Integration tests
* README documentation

## Explicitly Excluded

Do not implement:

* OpenAI
* Claude
* Ollama
* Any LLM
* Paid APIs
* Embeddings
* Vector databases
* Semantic search
* Summarization
* Paraphrasing
* Grammar correction
* Sentiment analysis
* Topic modelling
* YouTube titles
* YouTube descriptions
* LinkedIn posts
* Short-form hooks
* Portfolio notes
* Transcript file uploads
* Audio or video uploads
* Transcription
* PostgreSQL
* SQLAlchemy
* Redis
* Celery or RQ
* Background jobs
* Frontend
* Docker
* Authentication
* Future milestone infrastructure

## Required Endpoint

Create:

```text
POST /transcripts/analyze
```

The endpoint must accept the existing transcript request structure:

```json
{
  "text": "Transcript text"
}
```

Reuse `TranscriptCleanRequest`. Do not create an identical duplicate request model.

## Validation

The endpoint must preserve existing validation:

* `text` is required
* `text` must be a string
* minimum length is one character
* maximum length is 200,000 characters
* whitespace-only text is rejected
* invalid requests return FastAPI's standard `422` response

## Cleaning

Before analysis, call the existing transcript-cleaning service.

Do not duplicate the cleaning algorithm.

Analysis must operate on the final cleaned transcript.

## Sentence Detection

Split the cleaned transcript into meaningful sentence candidates using:

* sentence-ending punctuation: `.`, `?`, and `!`
* line boundaries

Requirements:

* preserve sentence-ending punctuation
* preserve capitalization
* preserve timestamps and speaker labels in returned key points
* discard empty fragments
* preserve original sentence order

## Tokenization

Use Python's standard library.

Requirements:

* lowercase tokens only for internal analysis
* ignore punctuation-only fragments
* ignore numeric-only tokens
* ignore timestamp fragments
* preserve apostrophes and hyphenated terms when practical
* do not alter the cleaned transcript

Do not install an NLP dependency.

## Stop Words

Create a small module-level immutable set of common English stop words.

Examples include:

```text
the
a
an
and
or
but
to
of
in
on
for
is
are
was
were
it
this
that
with
as
at
be
```

The list may include additional common function words when clearly documented.

Do not hide domain-specific words such as:

```text
api
ai
fastapi
python
content
automation
```

## Keyword Ranking

Count meaningful tokens across the cleaned transcript.

Return no more than ten keywords.

Rank using:

1. frequency descending
2. term alphabetically for equal frequencies

Each keyword must have:

```json
{
  "term": "keyword",
  "count": 2
}
```

Do not return duplicate terms.

## Sentence Scoring

Score each sentence using the frequencies of its meaningful tokens.

Use a deterministic length-normalized calculation equivalent to:

```text
sum(token frequency for meaningful sentence tokens)
divided by
number of meaningful sentence tokens
```

Sentences containing no meaningful tokens must receive a score of zero.

Do not use random values, model calls, embeddings, or semantic similarity.

## Key-Point Selection

Return no more than five key points.

Requirements:

* key points must be original transcript sentences
* do not rewrite or summarize sentences
* rank candidate sentences by score descending
* use original sentence position as the tie-breaker
* remove exact duplicate sentences
* after selection, return selected sentences in original transcript order
* return all meaningful sentences when fewer than five exist

## Required Response Models

Create in `backend/schemas/analysis.py`:

### `KeywordFrequency`

* `term: str`
* `count: int`

### `TranscriptAnalysis`

* `sentence_count: int`
* `unique_word_count: int`
* `top_keywords: list[KeywordFrequency]`
* `key_points: list[str]`

### `TranscriptAnalysisResponse`

* `cleaned_text: str`
* `metadata: TranscriptMetadata`
* `analysis: TranscriptAnalysis`

Reuse `TranscriptMetadata` from `backend/schemas/transcript.py`.

## Required Architecture

Create:

```text
backend/api/routes/analysis.py
backend/schemas/analysis.py
backend/services/content_analysis_service.py
tests/unit/test_content_analysis_service.py
tests/integration/test_analysis_api.py
```

Modify only:

```text
backend/main.py
README.md
```

Responsibilities:

### `backend/services/content_analysis_service.py`

* pure deterministic analysis
* call the existing transcript cleaner
* sentence detection
* tokenization
* stop-word filtering
* keyword ranking
* sentence scoring
* key-point selection
* metadata reuse or mapping
* no FastAPI route definitions
* no external side effects

### `backend/schemas/analysis.py`

* analysis response schemas only
* reuse existing transcript request and metadata schemas

### `backend/api/routes/analysis.py`

* `APIRouter`
* `POST /transcripts/analyze`
* existing request model
* declared response model
* thin route
* call analysis service
* map service result into response schema

### `backend/main.py`

* preserve existing app metadata
* preserve `GET /health`
* preserve transcript-cleaning route
* include the analysis router

## Dependencies

No new dependency should be required.

Use only:

* existing application dependencies
* Python standard library modules such as `re`, `collections`, and `dataclasses`

Do not modify `requirements.txt` unless a genuine requirement conflict is identified and explained before editing.

## Unit Tests

Create:

```text
tests/unit/test_content_analysis_service.py
```

Test:

1. punctuation-based sentence detection
2. line-based sentence detection
3. stop-word exclusion
4. numeric-only token exclusion
5. timestamp-fragment exclusion
6. keyword frequency ranking
7. alphabetical keyword tie-breaking
8. maximum of ten keywords
9. maximum of five key points
10. verbatim key-point wording
11. key points returned in transcript order
12. deterministic repeated output
13. one-sentence transcript
14. transcript containing mostly stop words

Tests may combine closely related behaviours when assertions remain clear.

## Integration Tests

Create:

```text
tests/integration/test_analysis_api.py
```

Test:

1. valid request returns `200`
2. response body matches the expected schema and values
3. cleaning is applied before analysis
4. whitespace-only input returns `422`
5. missing `text` returns `422`
6. oversized text returns `422`

All previous tests must continue to pass.

## README Changes

Update README with:

* Milestone 3 status
* deterministic transcript analysis feature
* endpoint method and path
* example request
* example response
* explanation of keywords and verbatim key points
* deterministic limitations
* test command
* statement that AI generation remains deferred

Do not claim that summarization or generated content exists.

## Commands

Run focused unit tests:

```powershell
python -m pytest tests/unit/test_content_analysis_service.py -q
```

Run focused integration tests:

```powershell
python -m pytest tests/integration/test_analysis_api.py -q
```

Run complete suite:

```powershell
python -m pytest -q
```

If necessary:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Acceptance Criteria

Milestone 3 is accepted only when:

1. Existing endpoints continue to work.
2. `POST /transcripts/analyze` accepts valid transcript text.
3. Existing validation is reused.
4. Existing transcript cleaning is reused.
5. Sentence detection is deterministic.
6. Keywords exclude configured stop words.
7. Keywords are ranked by frequency and alphabetical tie-breaking.
8. No more than ten keywords are returned.
9. No more than five key points are returned.
10. Key points use original sentence wording.
11. Key points are returned in transcript order.
12. Repeated requests return identical output.
13. Structured response validation works.
14. Unit tests pass.
15. Integration tests pass.
16. All previous tests pass.
17. README documentation matches the code.
18. No AI provider or paid API is required.
19. No future milestone infrastructure is introduced.
20. Codex reports every modified file and command.
21. The user manually verifies the endpoint.
22. The user creates and pushes the commit.

## Definition of Done

Milestone 3 is complete when the API can deterministically analyze a cleaned transcript, return ranked keywords and verbatim key points, pass the complete test suite, preserve all previous functionality, and the user has committed and pushed the verified implementation.
