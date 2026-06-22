# Release Checklist

## Repository State

- [ ] Git working tree is clean.
- [ ] `.env` is ignored.
- [ ] `.env.docker` is ignored.
- [ ] Model binaries under `models/` are ignored.
- [ ] Generated `artifacts/` output is ignored.
- [ ] No secrets, passwords, connection strings, or model binaries are staged.

## Verification

- [ ] Complete pytest suite passes.
- [ ] Deterministic evaluation passes.
- [ ] Docker Compose configuration validates.
- [ ] Core Compose smoke test passes.
- [ ] Media Compose smoke test passes when a model is mounted.
- [ ] README links point to existing tracked files.
- [ ] `git diff --check` passes.
- [ ] GitHub Actions passes after push.

## Documentation

- [ ] README is current.
- [ ] Architecture documentation is complete.
- [ ] Evaluation documentation and results are current.
- [ ] Portfolio case study is accurate.
- [ ] Resume bullets contain no fabricated metrics.
- [ ] Demo script is ready.
- [ ] Screenshot checklist is complete.
- [ ] Changelog and release notes are complete.

## Screenshots

- [ ] Generate preview captured.
- [ ] Generated assets captured.
- [ ] Saved history captured.
- [ ] Completed media job captured.
- [ ] API documentation or health endpoint captured.
- [ ] Docker Compose services captured.
- [ ] Tests passing captured.
- [ ] GitHub Actions captured after push.

## Manual Release

- [ ] Commit final Milestone 10 changes.
- [ ] Push the branch.
- [ ] Confirm GitHub Actions passed.
- [ ] Create annotated tag `v1.0.0`.
- [ ] Push tag `v1.0.0`.
- [ ] Create GitHub release using `docs/releases/v1.0.0.md`.

Codex must not create or push the tag or create the GitHub release unless explicitly asked.
