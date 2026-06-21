# Milestone 06 — PostgreSQL Persistence, Alembic Migrations, and History API

## Goal

Add production-style persistence to the AI Content Repurposing Pipeline.

This milestone combines:

* PostgreSQL configuration
* SQLAlchemy ORM models
* database session management
* Alembic schema migrations
* saved content generations
* paginated history retrieval
* full generation retrieval
* permanent generation deletion

## Existing Behaviour To Preserve

Preserve all existing endpoints:

* `GET /health`
* `POST /transcripts/clean`
* `POST /transcripts/analyze`
* `POST /content/brief`
* `POST /content/generate`

`POST /content/generate` must remain stateless and must not automatically persist data.

## New Endpoints

### Create And Save

```text
POST /generations
```

Use the existing `ContentGenerationRequest`.

The endpoint must:

1. run the existing content-generation workflow
2. validate the generated result
3. persist the complete request and output
4. return `201 Created`
5. return the saved ID, creation time, and complete generation

Do not duplicate generation logic.

### List History

```text
GET /generations
```

Query parameters:

* `limit: int = 20`, minimum 1, maximum 100
* `offset: int = 0`, minimum 0

Return:

* records ordered by `created_at` descending
* total record count
* current limit
* current offset

History items must contain:

* `id`
* `project_name`
* `provider`
* `project_summary`
* `created_at`

Do not return the original transcript or full Markdown export in list results.

### Retrieve One

```text
GET /generations/{generation_id}
```

Return the complete saved generation.

Return `404` when no matching record exists.

### Delete One

```text
DELETE /generations/{generation_id}
```

Return:

```text
204 No Content
```

Return `404` when no matching record exists.

Deletion is permanent.

## Database Model

Create one SQLAlchemy model named `Generation`.

Table name:

```text
generations
```

Fields:

* `id`: string UUID, primary key, maximum length 36
* `project_name`: string, required, maximum length 120
* `provider`: string, required, maximum length 32
* `input_text`: text, required
* `cleaned_text`: text, required
* `metadata_json`: generic JSON, required
* `analysis_json`: generic JSON, required
* `brief_json`: generic JSON, required
* `assets_json`: generic JSON, required
* `markdown_export`: text, required
* `created_at`: timezone-aware datetime, required

Generate IDs in Python using `uuid.uuid4()`.

Generate timestamps in Python using timezone-aware UTC datetimes.

Do not use PostgreSQL-specific UUID or JSONB types during this milestone because automated tests must remain portable to SQLite.

## Database Architecture

Create:

```text
backend/database/base.py
backend/database/session.py
backend/models/generation.py
backend/repositories/generation_repository.py
backend/services/generation_history_service.py
```

### Base

Use SQLAlchemy 2.x typed declarative mapping:

* `DeclarativeBase`
* `Mapped`
* `mapped_column`

### Session

Provide:

* lazy engine creation
* configured `sessionmaker`
* FastAPI session dependency using `yield`

The database engine must not be created at import time in a way that breaks existing non-database endpoints when `DATABASE_URL` is missing.

### Configuration

Add support for:

```text
DATABASE_URL=
```

`.env.example` must contain a placeholder such as:

```text
DATABASE_URL=postgresql+psycopg://postgres:change-me@localhost:5432/ai_content_pipeline
```

Do not include a real password.

When a database endpoint is used without database configuration, return a clear `503` error rather than crashing application import.

### Repository

Implement focused repository operations:

* create
* get by ID
* list with limit and offset
* count
* delete

Repository methods must not:

* call content providers
* know about FastAPI
* create HTTP exceptions
* commit unrelated operations

### Service

The history service must:

* call the existing generation service
* convert validated Pydantic output into ORM storage fields
* commit creation atomically
* roll back failed transactions
* reconstruct `ContentGenerationResponse` from stored JSON
* return history schemas
* retrieve records
* delete records

## Schemas

Create `backend/schemas/history.py`.

Required schemas:

### `GenerationHistoryItem`

* `id: str`
* `project_name: str`
* `provider: str`
* `project_summary: str`
* `created_at: datetime`

### `GenerationListResponse`

* `items: list[GenerationHistoryItem]`
* `total: int`
* `limit: int`
* `offset: int`

### `SavedGenerationResponse`

* `id: str`
* `created_at: datetime`
* `generation: ContentGenerationResponse`

Reuse existing generation schemas.

Do not duplicate asset, brief, analysis, or transcript schemas.

## Alembic

Create a standard Alembic environment:

```text
alembic.ini
migrations/env.py
migrations/script.py.mako
migrations/versions/
```

Requirements:

* load `.env`
* read `DATABASE_URL`
* import `Base.metadata`
* import application models so metadata is registered
* support online migrations
* support offline migration generation
* create one initial migration for the `generations` table
* include working `upgrade()` and `downgrade()` functions

Application runtime must not call:

```python
Base.metadata.create_all(...)
```

Schema changes belong to Alembic.

## Dependencies

Add only:

```text
sqlalchemy
alembic
psycopg[binary]
```

Do not add:

* asyncpg
* SQLModel
* Redis
* Celery
* Docker-related packages

## Error Handling

Create a database-layer or service-layer exception such as:

* `DatabaseConfigurationError`
* `DatabaseUnavailableError`
* `GenerationNotFoundError`

Map:

* missing database configuration → `503`
* unavailable database or failed connection → `503`
* unknown generation ID → `404`
* invalid request → existing `422`

Do not expose raw database passwords, connection strings, SQL statements, or internal exception details to API clients.

## Automated Tests

Automated tests must use temporary SQLite databases.

Do not require PostgreSQL for the test suite.

Use FastAPI dependency overrides for integration tests.

### Repository Tests

Test:

* create record
* get existing record
* missing record
* newest-first listing
* limit and offset
* total count
* delete
* delete missing record

### Service Tests

Test:

* existing generation workflow is reused
* complete output is serialized
* stored JSON reconstructs into valid Pydantic schemas
* commit occurs on success
* rollback occurs on failure
* retrieve existing record
* missing record handling
* deletion

### API Integration Tests

Test:

* `POST /generations` returns `201`
* saved response is complete
* default deterministic provider works
* `GET /generations` returns summaries
* pagination works
* list results exclude full transcript and Markdown
* `GET /generations/{id}` returns full record
* missing ID returns `404`
* deletion returns `204`
* deleted record later returns `404`
* missing database configuration returns `503`
* invalid request values preserve `422`
* all previous endpoints remain functional

### Migration Test

Test the initial migration against a temporary SQLite database:

1. upgrade to `head`
2. confirm `generations` table exists
3. downgrade to `base`
4. confirm table is removed

Do not require live PostgreSQL for migration tests.

## README

Document:

* PostgreSQL requirement for persistent local usage
* required `DATABASE_URL`
* dependency installation
* creating a database
* running `alembic upgrade head`
* migration commands
* creating a saved generation
* listing history
* retrieving one generation
* deleting one generation
* test database strategy
* current limitations

Do not claim Docker, authentication, background jobs, or multi-user storage exists.

## Commands

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run migrations:

```powershell
alembic upgrade head
```

Check migration state:

```powershell
alembic current
```

Run tests:

```powershell
python -m pytest -q
```

## Explicitly Excluded

Do not implement:

* authentication
* users
* ownership
* soft deletion
* record editing
* search
* filtering beyond pagination
* PostgreSQL full-text search
* Redis
* background jobs
* audio/video transcription
* frontend
* Docker
* deployment
* OpenAI
* Claude
* paid APIs

## Acceptance Criteria

Milestone 6 is complete when:

1. PostgreSQL configuration is supported.
2. SQLAlchemy models use modern typed mappings.
3. One session is provided per database request.
4. The schema is created by Alembic.
5. Existing stateless generation remains unchanged.
6. Saved generation creation returns `201`.
7. History listing is paginated and newest-first.
8. Full saved records can be retrieved.
9. Records can be permanently deleted.
10. Missing records return `404`.
11. Database configuration or connection problems return `503`.
12. Automated tests use isolated SQLite databases.
13. Migration upgrade and downgrade are tested.
14. All previous tests continue passing.
15. No Docker, queue, frontend, authentication, or paid API is added.
16. The user manually verifies PostgreSQL, migrations, endpoints, commit, and push.
