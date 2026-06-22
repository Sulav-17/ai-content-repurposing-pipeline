# Evaluation Results

## Summary

- Date: 2026-06-22
- Execution timestamp: 2026-06-22T20:11:30.379895+00:00
- Command: `.\.venv\Scripts\python.exe scripts\run_evaluation.py --output artifacts\evaluation-results.json`
- Cases: 8
- Passed: 8
- Failed: 0
- Overall status: passed

## Checked Behaviors

- Deterministic repeatability: passed for all cases.
- Schema validation: passed for all cases.
- YouTube title and short-hook counts: passed for all cases.
- Title and hook uniqueness: passed for all cases.
- Timestamp grounding: passed for all cases.
- Markdown section completeness: passed for all cases.
- Configured unsupported-claim guard checks: passed for all cases.
- Source keyword presence: passed for all cases.

## Evaluation Cases

- `technical-transcript`
- `timestamped-transcript`
- `sparse-transcript`
- `irregular-whitespace`
- `business-style-transcript`
- `source-numbers-claim-guard`
- `mixed-capitalization`
- `multi-format-source`

## Environment Notes

The evaluation used the deterministic provider only. It did not require PostgreSQL, Redis, Docker, Ollama, FFmpeg, whisper.cpp, a Whisper model, paid APIs, or network access. The generated JSON report was written to `artifacts/evaluation-results.json`, which is ignored by Git.
