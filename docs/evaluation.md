# Evaluation

## Purpose

The evaluation harness checks deterministic, mechanically verifiable behavior for the local content-generation pipeline. It is designed for release confidence, not for scoring creativity or semantic quality.

## What Is Evaluated

The harness loads eight synthetic cases from `tests/fixtures/evaluation_cases.json` and runs each through the existing public service boundary:

1. Construct `ContentGenerationRequest`.
2. Force provider `deterministic`.
3. Call the existing content-generation service.
4. Validate the existing `ContentGenerationResponse`.

It checks:

- response schema validity
- deterministic repeatability
- exactly five YouTube titles
- case-insensitive title uniqueness after trimming
- exactly five short hooks
- case-insensitive hook uniqueness after trimming
- short-form concept and portfolio-note limits
- nonblank required fields
- source-grounded chapter timestamps
- no chapters when the source has no timestamps
- expected concept grounding across generated fields
- required Markdown sections
- configured forbidden phrases and unsupported-claim patterns
- unsupported quantified claims that are not grounded in the source
- source keyword presence

## Why Deterministic Evaluation

The default provider is deterministic, local, and free of model calls. That makes the release evaluation repeatable on any machine with the Python dependencies installed. Optional Ollama output is intentionally excluded because local model selection and prompts can vary by operator.

## What The Checks Prove

The checks prove that the deterministic pipeline preserves core schema contracts, count limits, timestamp grounding, stable output, and basic claim guardrails for the configured cases.

## What The Checks Do Not Prove

The checks do not prove factual accuracy beyond source grounding, creative quality, publishing readiness, business performance, user adoption, revenue impact, or production reliability.

## Limitations

The evaluation uses keyword and pattern-based checks. It can catch obvious unsupported phrases and ungrounded quantified claims, but it cannot fully understand meaning, nuance, or tone. A human should review all generated content before publication.

## Rerun

```powershell
.\.venv\Scripts\python.exe scripts\run_evaluation.py --output artifacts\evaluation-results.json
```

The generated JSON report is ignored by Git.
