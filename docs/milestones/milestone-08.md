# Milestone 08 — Async Media Upload, Local Transcription, and Job Tracking

## Goal

Add a complete asynchronous media-processing workflow to the AI Content Repurposing Pipeline.

This milestone combines:

* audio and video upload
* secure temporary-file storage
* Redis queue configuration
* RQ background jobs
* local whisper.cpp transcription
* FFmpeg media conversion
* job-status and progress tracking
* optional content generation
* optional PostgreSQL persistence
* Streamlit media-job workflow

## Existing Behaviour To Preserve

Preserve all existing endpoints and frontend workflows.

Existing text generation must continue to work without Redis, FFmpeg, or whisper.cpp.

The application must not connect to Redis, load a model, or start subprocesses during module import.

## New API Endpoints

### Submit Media Job

```text
POST /media-jobs
```

Use multipart form data:

* `file`: required media upload
* `project_name`: required, trimmed, maximum 120 characters
* `provider`: `deterministic` or `ollama`, default `deterministic`
* `save_result`: boolean, default `true`
* `language`: optional trimmed language code

Return:

```text
202 Accepted
```

Response fields:

* `job_id`
* `status`
* `stage`
* `created_at`

### Retrieve Job

```text
GET /media-jobs/{job_id}
```

Return:

* `job_id`
* `status`
* `stage`
* `progress`
* `created_at`
* `started_at`
* `finished_at`
* safe user-facing error message when failed
* transcription result when finished
* generated content when finished
* saved generation ID when `save_result=true`

Unknown jobs return `404`.

### Cancel Queued Job

```text
DELETE /media-jobs/{job_id}
```

Requirements:

* queued jobs may be canceled
* canceling returns `204`
* unknown job returns `404`
* started or completed jobs return `409`
* delete the temporary upload when a queued job is canceled
* cancellation must not terminate an actively running subprocess unsafely

## Dependencies

Add only:

```text
redis
rq
python-multipart
```

Do not add:

* faster-whisper
* openai-whisper
* Celery
* Dramatiq
* Docker dependencies
* paid transcription APIs

FFmpeg and whisper.cpp are external local executables and must be configured through environment variables.

## Configuration

Add:

```env
REDIS_URL=redis://localhost:6379/0
RQ_QUEUE_NAME=media-processing
MEDIA_UPLOAD_DIR=.data/uploads
MEDIA_MAX_UPLOAD_MB=200
MEDIA_JOB_TIMEOUT_SECONDS=3600
MEDIA_JOB_RESULT_TTL_SECONDS=86400
MEDIA_JOB_FAILURE_TTL_SECONDS=86400

FFMPEG_EXECUTABLE=ffmpeg
WHISPER_CPP_EXECUTABLE=
WHISPER_CPP_MODEL_PATH=
WHISPER_CPP_THREADS=4
```

Requirements:

* load `.env`
* validate positive numeric settings
* do not require these values during application import
* return `503` when media-job functionality is used without Redis
* worker jobs must return safe configuration failures when FFmpeg, whisper.cpp, or the model is missing
* never include executable paths, Redis URLs, or internal exception messages in API errors

## Secure Upload Handling

Create a dedicated upload service.

Requirements:

* allow only documented extensions
* validate declared content type where available
* enforce maximum size while streaming
* do not load the entire upload into memory
* generate a UUID storage filename
* preserve only an approved lowercase suffix
* never use the original filename as a filesystem path
* create the upload directory lazily
* reject empty files
* delete partial files when validation or writing fails
* delete uploaded and converted files after completion or failure
* delete uploaded files when enqueueing fails

Do not trust the client filename.

## Queue Architecture

Create lazy Redis and RQ helpers.

Requirements:

* no Redis connection at import time
* no queue creation requiring a live Redis connection at import time
* provide test reset helpers
* enqueue a top-level importable worker function
* include job timeout and result/failure TTLs
* store progress and stage information in RQ job metadata
* update metadata at meaningful processing stages
* use safe serialization values only

Do not place database sessions or HTTP clients into RQ job arguments.

## Worker Workflow

The worker function must:

1. mark the job as started
2. convert the uploaded file to a safe WAV file
3. transcribe the WAV file locally
4. produce a normalized transcript
5. call the existing content-generation workflow
6. optionally save through the existing history service
7. return a validated job result
8. clean temporary files in `finally`

When `save_result=false`, do not create a PostgreSQL record.

When `save_result=true`, create a database session inside the worker and commit through the existing history-service transaction boundary.

Do not duplicate transcript cleaning, analysis, brief generation, asset generation, Markdown export, or persistence serialization.

## FFmpeg Conversion

Create a media-conversion service.

Requirements:

* invoke a configured executable using an argument list
* use `shell=False`
* convert to:

  * WAV
  * mono
  * 16 kHz
  * signed 16-bit PCM
* enforce a timeout
* capture output without displaying it to clients
* reject failed conversion
* delete incomplete output
* never execute user-provided command arguments

All subprocess calls must be mocked in tests.

## Local Transcription Provider

Create a transcription protocol and a `WhisperCppTranscriber`.

Requirements:

* configure executable and model paths
* validate that configured files exist before execution
* use `shell=False`
* provide only application-controlled arguments
* support an optional language
* enforce a timeout
* parse transcript text and timestamped segments
* normalize whitespace
* reject blank transcription output
* return a validated transcription schema
* map missing configuration to a safe configuration error
* map process failure, timeout, or malformed output to a safe transcription error

The provider must not download models automatically.

## Job Result Schemas

Create schemas such as:

### `TranscriptionSegment`

* `start_seconds`
* `end_seconds`
* `text`

Validate:

* nonnegative times
* end greater than or equal to start
* nonblank text

### `TranscriptionResult`

* `text`
* `segments`
* `language` when available

### `MediaJobSubmissionResponse`

* `job_id`
* `status`
* `stage`
* `created_at`

### `MediaJobStatusResponse`

* job metadata
* transcription when finished
* generation when finished
* saved generation ID when applicable
* safe error message when failed

Do not expose RQ objects directly.

## Error Handling

Create safe exceptions for:

* queue configuration
* Redis unavailable
* upload validation
* media conversion
* transcription configuration
* transcription failure
* job not found
* job conflict

Map:

* invalid upload or form data → `400` or `422`
* oversized upload → `413`
* missing Redis or Redis unavailable → `503`
* unknown job → `404`
* noncancelable job → `409`

Worker failures should normally be represented by a failed job status, not by leaking an exception through the status endpoint.

## Streamlit Frontend

Add a third tab:

```text
Media Jobs
```

Provide:

* project-name input
* media file uploader
* provider selector
* save-result checkbox
* optional language input
* submit button
* current job ID
* status
* stage
* progress
* refresh-status button
* cancel button for queued jobs
* transcription display
* structured content rendering on completion
* saved generation ID when persisted
* Markdown download

Requirements:

* use the existing HTTP API client
* do not access Redis, worker code, transcription providers, filesystems, or database services directly
* store only serializable job state
* do not create automatic rerun loops
* manually refresh status
* use the existing result renderer for completed generation output
* handle API, queue, worker, provider, and database failures safely

## Files To Create

```text
backend/api/routes/media_jobs.py
backend/schemas/media_jobs.py
backend/services/media_upload_service.py
backend/services/media_conversion_service.py
backend/services/media_job_service.py

backend/transcription/__init__.py
backend/transcription/base.py
backend/transcription/whisper_cpp.py

backend/queueing/__init__.py
backend/queueing/connection.py

backend/jobs/__init__.py
backend/jobs/media_processing.py

tests/unit/test_media_upload_service.py
tests/unit/test_media_conversion_service.py
tests/unit/test_whisper_cpp_transcriber.py
tests/unit/test_media_job_service.py
tests/unit/test_media_processing_job.py
tests/integration/test_media_jobs_api.py
tests/unit/test_frontend_media_jobs.py
tests/integration/test_streamlit_media_jobs.py
```

## Files To Modify

```text
backend/core/config.py
backend/main.py
frontend/api_client.py
frontend/renderers.py
frontend/app.py
requirements.txt
.env.example
.gitignore
README.md
```

## Automated Tests

Tests must not require:

* live Redis
* a running RQ worker
* FFmpeg
* whisper.cpp
* a Whisper model
* PostgreSQL
* Ollama
* internet access

Mock:

* Redis
* RQ
* subprocess calls
* filesystem failures where applicable
* transcription output
* content providers
* frontend HTTP calls

Test:

* allowed and rejected upload types
* empty uploads
* maximum-size enforcement
* UUID filenames
* path-traversal prevention
* partial-file cleanup
* enqueue success and failure cleanup
* Redis configuration and unavailable errors
* correct job arguments and TTLs
* conversion argument safety
* `shell=False`
* conversion timeout/failure
* transcription configuration
* transcript parsing
* blank/malformed transcript rejection
* job-stage and progress updates
* generated content reuse
* optional persistence
* file cleanup after success/failure
* submit endpoint returns `202`
* status endpoint
* failed-job safe message
* unknown job `404`
* cancellation `204`
* started-job conflict `409`
* frontend upload controls
* frontend status refresh
* completed-result rendering
* no prohibited direct imports

All previous tests must continue passing.

## Explicitly Excluded

Do not implement:

* live microphone streaming
* speaker diarization
* subtitle editing
* translation
* cloud transcription APIs
* OpenAI transcription
* automatic model downloads
* Celery
* Docker
* deployment
* authentication
* multiple users
* social-media publishing
* automatic video clipping

## Acceptance Criteria

Milestone 8 is complete when:

1. Media uploads return `202`.
2. Jobs are placed into an RQ queue.
3. Status and progress can be retrieved.
4. A local worker converts and transcribes media.
5. Existing generation logic processes the transcript.
6. Results may optionally be saved to PostgreSQL.
7. Temporary files are cleaned.
8. Queue and worker failures are safely represented.
9. Queued jobs can be canceled.
10. Streamlit supports upload and job tracking.
11. Automated tests require no live external services.
12. Existing workflows remain operational.
13. No paid API or future milestone infrastructure is added.
14. Manual verification, commit, and push are completed.
