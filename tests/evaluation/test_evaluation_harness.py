import json

import pytest

from backend.schemas.generation import ContentGenerationRequest
from backend.services.content_generation_service import generate_content_assets
from scripts.run_evaluation import (
    EvaluationCase,
    evaluate_case,
    evaluate_response,
    load_evaluation_cases,
    run_evaluation,
)


def test_load_evaluation_cases_validates_fixture_structure() -> None:
    cases = load_evaluation_cases()

    assert len(cases) == 8
    assert len({case.id for case in cases}) == 8
    assert all(case.project_name for case in cases)
    assert all(case.text for case in cases)
    assert all(case.expected_concepts for case in cases)


def test_load_evaluation_cases_rejects_duplicate_ids(tmp_path) -> None:
    fixture_path = tmp_path / "cases.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "id": "duplicate",
                    "project_name": "One",
                    "text": "Host: One.",
                    "expected_concepts": ["one"],
                    "expects_timestamps": False,
                    "forbidden_phrases": [],
                    "unsupported_claim_patterns": [],
                },
                {
                    "id": "duplicate",
                    "project_name": "Two",
                    "text": "Host: Two.",
                    "expected_concepts": ["two"],
                    "expects_timestamps": False,
                    "forbidden_phrases": [],
                    "unsupported_claim_patterns": [],
                },
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate"):
        load_evaluation_cases(fixture_path)


def test_every_evaluation_case_produces_valid_structured_response() -> None:
    for case in load_evaluation_cases():
        request = ContentGenerationRequest(
            text=case.text,
            project_name=case.project_name,
            provider="deterministic",
        )

        response = generate_content_assets(
            text=request.text,
            project_name=request.project_name,
            provider_name=request.provider,
        )
        result = evaluate_response(case, response)

        assert result["passed"], result["failure_reasons"]


def test_evaluation_repeated_runs_are_deterministic() -> None:
    for case in load_evaluation_cases():
        result = evaluate_case(case)

        deterministic = [
            check for check in result["checks"] if check["name"] == "deterministic_repeatability"
        ][0]
        assert deterministic["passed"]


def test_evaluation_checks_counts_uniqueness_timestamps_markdown_and_claims() -> None:
    report = run_evaluation()

    assert report["status"] == "passed"
    assert report["total_cases"] == 8
    assert report["failed_count"] == 0
    for case_result in report["cases"]:
        check_names = {check["name"] for check in case_result["checks"]}
        assert "youtube_title_count" in check_names
        assert "youtube_title_uniqueness" in check_names
        assert "short_hook_count" in check_names
        assert "short_hook_uniqueness" in check_names
        assert "timestamp_grounding" in check_names
        assert "required_markdown_sections" in check_names
        assert "configured_claim_pattern_guard" in check_names
        assert "source_keyword_presence" in check_names


def test_timestamped_case_has_grounded_chapters_and_untimestamped_cases_have_none() -> None:
    for case in load_evaluation_cases():
        response = generate_content_assets(
            text=case.text,
            project_name=case.project_name,
            provider_name="deterministic",
        )

        if case.expects_timestamps:
            assert response.assets.youtube_chapters
        else:
            assert response.assets.youtube_chapters == []


def test_evaluate_response_returns_failure_for_invalid_result() -> None:
    case = EvaluationCase(
        id="invalid",
        project_name="Invalid",
        text="Host: FastAPI validates outputs.",
        expected_concepts=("fastapi",),
        expects_timestamps=False,
        forbidden_phrases=(),
        unsupported_claim_patterns=(),
    )
    response = generate_content_assets(
        text=case.text,
        project_name=case.project_name,
        provider_name="deterministic",
    )
    response.assets.youtube_titles = response.assets.youtube_titles[:1]

    result = evaluate_response(case, response)

    assert not result["passed"]
    assert "Expected exactly five YouTube titles." in result["failure_reasons"]
