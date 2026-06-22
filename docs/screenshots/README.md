# Screenshot Checklist

Codex must not fabricate screenshots. Capture real screenshots from your local environment and redact sensitive details.

## `01-generate-preview.png`

- Open: Streamlit Generate tab.
- Show: project name, transcript input, provider, and generated preview.
- Hide: personal transcript text, secrets, local paths.
- Crop: browser content area.

## `02-generated-assets.png`

- Open: generated result sections.
- Show: content brief, YouTube assets, LinkedIn post, hooks, concepts, notes, and Markdown preview.
- Hide: any private source text.
- Crop: generated content area.

## `03-saved-history.png`

- Open: Saved History tab.
- Show: saved records, pagination, open/download/delete controls.
- Hide: record IDs if you prefer not to show them.
- Crop: history list.

## `04-media-job-complete.png`

- Open: Media Jobs tab after a completed job.
- Show: status `finished`, stage `complete`, progress `100`, transcript preview, and generated content.
- Hide: local filenames, paths, and personal media names.
- Crop: status and result area.

## `05-api-swagger.png`

- Open: FastAPI docs at `/docs`.
- Show: endpoint groups.
- Hide: local browser profile details.
- Crop: API documentation list.

## `06-docker-compose-services.png`

- Open: terminal running `docker compose --env-file .env.docker --profile media ps`.
- Show: service names and health/status.
- Hide: credentials, full connection strings, and unrelated terminal history.
- Crop: command output.

## `07-tests-passing.png`

- Open: terminal after the final pytest or evaluation command.
- Show: exact pass count and command.
- Hide: machine-specific prompt paths if desired.
- Crop: command and result.

## `08-github-actions.png`

- Open: GitHub Actions workflow after push.
- Show: CI job success.
- Hide: unrelated repository tabs or private browser details.
- Crop: workflow result area.
