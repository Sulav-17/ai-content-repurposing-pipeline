# Milestone 07 — Streamlit Frontend and Saved-History Workflow

## Goal

Build a complete Streamlit frontend for the AI Content Repurposing Pipeline.

This milestone combines:

* stateless content generation
* saved content generation
* structured result presentation
* Markdown preview and download
* saved-history browsing
* pagination
* full-record retrieval
* permanent deletion
* frontend error handling
* automated frontend tests

## Existing Backend Endpoints

The frontend must use:

* `GET /health`
* `POST /content/generate`
* `POST /generations`
* `GET /generations`
* `GET /generations/{generation_id}`
* `DELETE /generations/{generation_id}`

Do not call transcript-clean, transcript-analysis, or content-brief endpoints directly from the primary user workflow.

## Architecture

The Streamlit frontend must communicate with FastAPI over HTTP.

It must not directly import or access:

* database sessions
* SQLAlchemy models
* repositories
* Alembic
* backend service functions
* provider implementations

The FastAPI API remains the application boundary.

## Configuration

Add:

```env
API_BASE_URL=http://127.0.0.1:8000
API_TIMEOUT_SECONDS=30
```

Requirements:

* load local `.env`
* use a safe localhost default
* strip trailing slashes from the base URL
* validate that timeout is positive
* do not include credentials
* do not hard-code database URLs in frontend code

## API Client

Create:

```text
frontend/api_client.py
```

Provide focused operations:

* `health_check()`
* `generate_preview(request)`
* `generate_and_save(request)`
* `list_generations(limit, offset)`
* `get_generation(generation_id)`
* `delete_generation(generation_id)`

Requirements:

* use `httpx`
* use configured timeouts
* centralize request handling
* parse JSON responses
* return Python dictionaries or validated frontend-facing structures
* handle `204 No Content`
* never expose raw stack traces or connection strings to users

Create frontend exceptions such as:

* `FrontendConfigurationError`
* `ApiUnavailableError`
* `ApiRequestError`
* `ApiResponseError`

The client must distinguish:

* connection and timeout errors
* backend validation errors
* provider errors
* database errors
* malformed backend responses

## Streamlit Application

Create:

```text
frontend/app.py
```

Use a clear page title and wide layout.

Display backend health near the top of the application.

The main interface must contain two tabs:

1. Generate
2. Saved History

## Generate Tab

Inputs:

* project name
* transcript text
* provider selection:

  * `deterministic`
  * `ollama`

Actions:

### Generate Preview

Call:

```text
POST /content/generate
```

Do not save the result.

### Generate And Save

Call:

```text
POST /generations
```

Persist and return the saved record.

Validation:

* project name is required
* transcript is required
* disable or reject submission when either is blank
* display clear validation messages
* do not send invalid requests unnecessarily

During requests:

* display a progress indicator or spinner
* prevent duplicate handling from a single click
* display concise success or failure feedback

## Result Rendering

Create reusable rendering helpers in:

```text
frontend/renderers.py
```

Render:

* project summary
* provider
* saved ID and creation time when present
* content brief
* key takeaways
* source keywords
* YouTube titles
* YouTube description
* YouTube chapters
* LinkedIn post
* short-form hooks
* short-form concepts
* portfolio notes
* Markdown preview

Use:

* sections
* expanders
* bullets
* numbered lists
* code or text areas where copying is useful

Do not render raw JSON as the primary user experience.

A debug JSON expander may be included but must not replace structured rendering.

## Markdown Download

Provide a download button for the generated Markdown.

Filename requirements:

* derive from project name
* lowercase or otherwise normalize safely
* replace unsafe filename characters
* use `.md`
* use a fallback such as `content-export.md`

Examples:

```text
ai-content-repurposing-pipeline.md
local-content-pipeline.md
```

## Session State

Use session state only for transient frontend state such as:

* latest generated result
* selected history record
* current history page
* deletion confirmation state
* success messages that must survive one rerun

Do not treat session state as permanent storage.

Do not place database sessions, HTTP clients, secrets, or unserializable resources in session state.

## Saved History Tab

Fetch:

```text
GET /generations?limit=<limit>&offset=<offset>
```

Show:

* project name
* provider
* project summary
* creation time
* total saved count

Requirements:

* newest first, as returned by the API
* default page size such as 10
* previous and next controls
* prevent negative offsets
* disable next when no more records exist
* retain the current page during normal reruns
* provide a refresh action

Each history item must allow the user to:

* open the full saved record
* download its Markdown
* request permanent deletion

## Full Saved Record

Fetch:

```text
GET /generations/{generation_id}
```

Render using the same result renderer as newly generated content.

Do not duplicate result-rendering logic.

## Deletion

Deletion is permanent.

Requirements:

1. the first action requests confirmation
2. display the project name or record ID being deleted
3. provide explicit confirm and cancel actions
4. call `DELETE /generations/{generation_id}` only after confirmation
5. clear the selected record after successful deletion
6. refresh history
7. adjust pagination when deleting the final record on a page
8. display success or failure feedback

Do not delete immediately from a single unconfirmed click.

## Error Handling

Display user-friendly messages for:

* FastAPI unavailable
* request timeout
* invalid transcript or project name
* Ollama unconfigured
* Ollama unavailable
* database unconfigured
* PostgreSQL unavailable
* missing saved record
* malformed backend response

Do not display:

* Python tracebacks
* database passwords
* full database URLs
* raw SQL
* internal provider exception details

The frontend itself should still load when the backend is unavailable.

## Automated Tests

### API Client Tests

Mock all HTTP calls.

Test:

* correct URL construction
* trailing-slash normalization
* preview request
* saved request
* list pagination parameters
* full-record retrieval
* deletion and `204`
* timeout handling
* connection failure handling
* non-success status handling
* validation-error message extraction
* malformed JSON handling
* no credentials leaked in exceptions

### Renderer Tests

Test pure helper functions such as:

* safe Markdown filename generation
* history-page offset calculation
* next-page availability
* saved-response unwrapping
* empty chapter handling
* malformed response rejection where applicable

Keep logic outside Streamlit widgets when it can be tested as a pure function.

### Streamlit App Tests

Use Streamlit’s headless application-testing support.

Test at minimum:

* application loads without a live backend
* Generate and Saved History tabs exist
* project-name input exists
* transcript input exists
* provider control exists
* preview and save actions exist
* backend-unavailable state is shown without crashing
* no database or backend internals are imported directly by the frontend

Mock or isolate all network access.

Automated tests must not require:

* a running FastAPI server
* PostgreSQL
* Ollama
* internet access

## Dependencies

Add only:

```text
streamlit
```

unless it already exists.

Do not add a frontend JavaScript framework.

## README

Document:

* backend setup
* PostgreSQL setup
* Alembic migration
* starting FastAPI
* starting Streamlit
* using Generate Preview
* using Generate and Save
* browsing history
* downloading Markdown
* deleting a record
* optional Ollama usage
* current limitations

Recommended local commands:

```powershell
python -m uvicorn backend.main:app --reload
python -m streamlit run frontend/app.py
```

The two processes should run in separate terminals.

## Explicitly Excluded

Do not implement:

* React
* Next.js
* authentication
* multiple users
* database access from the frontend
* uploads
* audio or video transcription
* background jobs
* Redis
* Celery
* Docker
* deployment
* social-media publishing
* OpenAI
* Claude
* paid APIs
* editing saved records

## Acceptance Criteria

Milestone 7 is complete when:

1. The Streamlit frontend loads locally.
2. Backend health is displayed.
3. Users can generate an unsaved preview.
4. Users can generate and save a record.
5. Structured assets are rendered clearly.
6. Markdown can be downloaded.
7. Saved history is paginated.
8. Full saved records can be opened.
9. Deletion requires confirmation.
10. Deleted records disappear from history.
11. Backend, provider, and database failures are handled safely.
12. The frontend accesses the application only through HTTP.
13. Automated tests require no live services.
14. All previous backend tests continue passing.
15. No future milestone infrastructure is added.
16. The implementation is manually verified, committed, and pushed.
