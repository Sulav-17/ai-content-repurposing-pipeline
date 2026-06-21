# Repository Instructions for Codex

## Purpose

This repository contains the AI Content Repurposing Pipeline.

The project is developed one approved milestone at a time. Milestone specifications are stored in `docs/milestones/`.

## Required Workflow

1. Read this `AGENTS.md` file before making changes.
2. Read the milestone specification named in the current task.
3. Inspect the existing repository before proposing changes.
4. Explain the proposed implementation before editing unless the user explicitly says that the plan has already been approved.
5. Wait for approval before editing when approval is requested.
6. Work only on the current milestone.
7. Do not implement future milestones.
8. Do not modify unrelated files.

## Scope Control

* Treat the current milestone specification as the source of truth.
* Do not add features, folders, dependencies, infrastructure, or abstractions that are not required by the current milestone.
* Ask for clarification when a requirement is genuinely contradictory.
* Prefer the simplest implementation that fully satisfies the acceptance criteria.
* Do not perform broad refactoring unless the milestone requires it.

## Code Quality

* Keep code readable for a beginner-to-intermediate Python developer.
* Use clear function, module, and variable names.
* Add type hints to application code where appropriate.
* Keep functions focused on one responsibility.
* Avoid unnecessary abstraction.
* Follow the repository's existing architecture and naming conventions.
* Inspect existing implementations before creating duplicate utilities.

## Dependencies

* Do not add a dependency without explaining why it is required.
* Do not add technologies assigned to future milestones.
* Keep dependency files accurate when dependencies change.

## Testing

* Add or update tests for important behavior introduced by the milestone.
* Run the smallest relevant test set during development.
* Run the full configured test suite before reporting completion when practical.
* Report the exact test command and result.
* Do not claim that tests passed unless they were actually executed successfully.

## Security and Configuration

* Never hardcode API keys, passwords, tokens, or credentials.
* Never expose or commit `.env`.
* Document required environment variables in `.env.example`.
* Do not place real secrets in examples, tests, logs, or documentation.
* Do not execute arbitrary LLM-generated code.

## Git Rules

* Do not commit changes unless the user explicitly asks.
* Do not push changes unless the user explicitly asks.
* Do not discard or overwrite unrelated user work.
* Do not rewrite Git history.
* Show or summarize the final working-tree changes.

## Completion Report

After implementation:

1. Summarize every created, modified, or deleted file.
2. List all commands executed.
3. Report test results.
4. Explain deviations from the approved plan.
5. Report remaining limitations or unresolved issues.
6. Confirm that no future milestone work was implemented.
