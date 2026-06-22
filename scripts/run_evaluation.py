import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.schemas.generation import ContentGenerationRequest, ContentGenerationResponse
from backend.services.content_generation_service import extract_timestamps, generate_content_assets


REQUIRED_MARKDOWN_SECTIONS = (
    "## Project Summary",
    "## Content Brief",
    "## YouTube Titles",
    "## YouTube Description",
    "## YouTube Chapters",
    "## LinkedIn Post",
    "## Short-Form Hooks",
    "## Short-Form Video Concepts",
    "## Portfolio Notes",
    "## Source Keywords",
)
QUANTIFIED_CLAIM_PATTERN = re.compile(
    r"\b(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>%|percent|users|customers|revenue|growth|hours|minutes|times|x)\b",
    re.IGNORECASE,
)
DEFAULT_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "evaluation_cases.json"


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    project_name: str
    text: str
    expected_concepts: tuple[str, ...]
    expects_timestamps: bool
    forbidden_phrases: tuple[str, ...]
    unsupported_claim_patterns: tuple[str, ...]


def load_evaluation_cases(path: str | Path = DEFAULT_FIXTURE_PATH) -> list[EvaluationCase]:
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise ValueError("Evaluation fixture must be a list of cases.")

    cases: list[EvaluationCase] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Evaluation case at index {index} must be an object.")

        case_id = _required_string(item, "id", index)
        if case_id in seen_ids:
            raise ValueError(f"Duplicate evaluation case id: {case_id}")
        seen_ids.add(case_id)

        cases.append(
            EvaluationCase(
                id=case_id,
                project_name=_required_string(item, "project_name", index),
                text=_required_string(item, "text", index),
                expected_concepts=_required_string_tuple(item, "expected_concepts", index),
                expects_timestamps=_required_bool(item, "expects_timestamps", index),
                forbidden_phrases=_string_tuple(item, "forbidden_phrases", index),
                unsupported_claim_patterns=_string_tuple(item, "unsupported_claim_patterns", index),
            )
        )

    return cases


def evaluate_case(case: EvaluationCase) -> dict[str, Any]:
    request = ContentGenerationRequest(
        text=case.text,
        project_name=case.project_name,
        provider="deterministic",
    )
    first_response = generate_content_assets(
        text=request.text,
        project_name=request.project_name,
        provider_name=request.provider,
    )
    second_response = generate_content_assets(
        text=request.text,
        project_name=request.project_name,
        provider_name=request.provider,
    )
    result = evaluate_response(case, first_response)
    deterministic_check = _check(
        "deterministic_repeatability",
        first_response.model_dump(mode="json") == second_response.model_dump(mode="json"),
        "Repeated deterministic output changed.",
    )
    result["checks"].insert(1, deterministic_check)
    result["passed"] = all(check["passed"] for check in result["checks"])
    result["failure_reasons"] = [
        check["reason"] for check in result["checks"] if not check["passed"] and check["reason"]
    ]
    return result


def evaluate_response(case: EvaluationCase, response: ContentGenerationResponse) -> dict[str, Any]:
    source_timestamps = extract_timestamps(response.cleaned_text)
    response_payload = response.model_dump(mode="json")
    content_for_concepts = _content_for_concepts(response)
    content_for_claims = _content_for_claims(response)
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?", response.cleaned_text))

    checks = [
        _check_schema(response_payload),
        _check(
            "youtube_title_count",
            len(response.assets.youtube_titles) == 5,
            "Expected exactly five YouTube titles.",
        ),
        _check_unique("youtube_title_uniqueness", response.assets.youtube_titles, "YouTube titles"),
        _check(
            "short_hook_count",
            len(response.assets.short_hooks) == 5,
            "Expected exactly five short hooks.",
        ),
        _check_unique("short_hook_uniqueness", response.assets.short_hooks, "Short hooks"),
        _check(
            "short_form_concept_limit",
            3 <= len(response.assets.short_form_concepts) <= 5,
            "Expected three to five short-form concepts.",
        ),
        _check(
            "portfolio_note_limit",
            3 <= len(response.assets.portfolio_notes) <= 8,
            "Expected three to eight portfolio notes.",
        ),
        _check_nonblank_required_fields(response),
        _check_timestamp_expectation(case, source_timestamps),
        _check_chapter_grounding(case, response, source_timestamps),
        _check_expected_concepts(case, content_for_concepts),
        _check_markdown_sections(response.markdown_export),
        _check_forbidden_phrases(case, content_for_claims),
        _check_forbidden_patterns(case, content_for_claims),
        _check_unsupported_quantified_claims(content_for_claims, source_numbers),
        _check_source_keywords(response),
    ]
    return {
        "case_id": case.id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "failure_reasons": [
            check["reason"] for check in checks if not check["passed"] and check["reason"]
        ],
    }


def run_evaluation(cases: list[EvaluationCase] | None = None) -> dict[str, Any]:
    selected_cases = cases or load_evaluation_cases()
    results = [evaluate_case(case) for case in selected_cases]
    passed_count = sum(1 for result in results if result["passed"])
    failed_count = len(results) - passed_count
    return {
        "executed_at": datetime.now(UTC).isoformat(),
        "total_cases": len(results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "status": "passed" if failed_count == 0 else "failed",
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic pipeline evaluation.")
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_FIXTURE_PATH),
        help="Path to the evaluation fixture JSON file.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for a JSON evaluation report.",
    )
    args = parser.parse_args()

    try:
        report = run_evaluation(load_evaluation_cases(args.cases))
    except Exception as exc:
        print(f"Evaluation failed to run: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        "Evaluation {status}: {passed}/{total} cases passed.".format(
            status=report["status"],
            passed=report["passed_count"],
            total=report["total_cases"],
        )
    )
    for case_result in report["cases"]:
        status = "PASS" if case_result["passed"] else "FAIL"
        print(f"- {case_result['case_id']}: {status}")
        for reason in case_result["failure_reasons"]:
            print(f"  - {reason}")

    return 0 if report["failed_count"] == 0 else 1


def _required_string(item: dict[str, Any], key: str, index: int) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Evaluation case {index} field {key} must be a nonblank string.")
    return value.strip()


def _required_string_tuple(item: dict[str, Any], key: str, index: int) -> tuple[str, ...]:
    values = _string_tuple(item, key, index)
    if not values:
        raise ValueError(f"Evaluation case {index} field {key} must not be empty.")
    return values


def _string_tuple(item: dict[str, Any], key: str, index: int) -> tuple[str, ...]:
    values = item.get(key)
    if not isinstance(values, list):
        raise ValueError(f"Evaluation case {index} field {key} must be a list.")
    normalized_values: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Evaluation case {index} field {key} must contain nonblank strings.")
        normalized_values.append(value.strip())
    return tuple(normalized_values)


def _required_bool(item: dict[str, Any], key: str, index: int) -> bool:
    value = item.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Evaluation case {index} field {key} must be a boolean.")
    return value


def _check_schema(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        ContentGenerationResponse.model_validate(payload)
    except ValidationError:
        return _check("valid_response_schema", False, "Response failed ContentGenerationResponse validation.")
    return _check("valid_response_schema", True, "")


def _check_unique(name: str, values: list[str], label: str) -> dict[str, Any]:
    normalized_values = [value.strip().casefold() for value in values]
    return _check(
        name,
        len(normalized_values) == len(set(normalized_values)),
        f"{label} were not unique after trimming and case normalization.",
    )


def _check_nonblank_required_fields(response: ContentGenerationResponse) -> dict[str, Any]:
    values = [
        response.provider,
        response.project_name,
        response.cleaned_text,
        response.brief.summary,
        response.brief.core_message,
        response.brief.target_audience,
        response.brief.suggested_tone,
        response.assets.youtube_description,
        response.assets.linkedin_post,
        response.assets.project_summary,
        response.markdown_export,
        *response.brief.key_takeaways,
        *response.brief.source_keywords,
        *response.assets.youtube_titles,
        *response.assets.short_hooks,
        *response.assets.short_form_concepts,
        *response.assets.portfolio_notes,
    ]
    return _check(
        "nonblank_required_fields",
        all(isinstance(value, str) and value.strip() for value in values),
        "One or more required string fields were blank.",
    )


def _check_timestamp_expectation(case: EvaluationCase, source_timestamps: list[str]) -> dict[str, Any]:
    return _check(
        "timestamp_expectation",
        bool(source_timestamps) == case.expects_timestamps,
        "Source timestamp expectation did not match cleaned transcript.",
    )


def _check_chapter_grounding(
    case: EvaluationCase,
    response: ContentGenerationResponse,
    source_timestamps: list[str],
) -> dict[str, Any]:
    source_timestamp_set = set(source_timestamps)
    chapter_timestamps = [chapter.timestamp.strip().strip("[]") for chapter in response.assets.youtube_chapters]
    if not source_timestamp_set and chapter_timestamps:
        return _check("timestamp_grounding", False, "Chapters were returned without source timestamps.")
    if any(timestamp not in source_timestamp_set for timestamp in chapter_timestamps):
        return _check("timestamp_grounding", False, "A chapter timestamp was not present in the source transcript.")
    if case.expects_timestamps and not chapter_timestamps:
        return _check("timestamp_grounding", False, "Expected source-grounded chapters for timestamped transcript.")
    return _check("timestamp_grounding", True, "")


def _check_expected_concepts(case: EvaluationCase, normalized_content: str) -> dict[str, Any]:
    missing = [
        concept for concept in case.expected_concepts if _normalize(concept) not in normalized_content
    ]
    return _check(
        "expected_concept_grounding",
        not missing,
        "Missing expected grounded concepts: " + ", ".join(missing) if missing else "",
    )


def _check_markdown_sections(markdown_export: str) -> dict[str, Any]:
    missing = [section for section in REQUIRED_MARKDOWN_SECTIONS if section not in markdown_export]
    return _check(
        "required_markdown_sections",
        not missing,
        "Missing Markdown sections: " + ", ".join(missing) if missing else "",
    )


def _check_forbidden_phrases(case: EvaluationCase, normalized_content: str) -> dict[str, Any]:
    matches = [
        phrase for phrase in case.forbidden_phrases if _normalize(phrase) in normalized_content
    ]
    return _check(
        "forbidden_phrase_guard",
        not matches,
        "Forbidden phrase appeared: " + ", ".join(matches) if matches else "",
    )


def _check_forbidden_patterns(case: EvaluationCase, content: str) -> dict[str, Any]:
    matches = []
    for pattern in case.unsupported_claim_patterns:
        if re.search(pattern, content, flags=re.IGNORECASE):
            matches.append(pattern)
    return _check(
        "configured_claim_pattern_guard",
        not matches,
        "Configured unsupported claim pattern matched: " + ", ".join(matches) if matches else "",
    )


def _check_unsupported_quantified_claims(content: str, source_numbers: set[str]) -> dict[str, Any]:
    ungrounded = []
    for match in QUANTIFIED_CLAIM_PATTERN.finditer(content):
        if match.group("number") not in source_numbers:
            ungrounded.append(match.group(0))
    return _check(
        "unsupported_quantified_claim_guard",
        not ungrounded,
        "Ungrounded quantified claim appeared: " + ", ".join(ungrounded) if ungrounded else "",
    )


def _check_source_keywords(response: ContentGenerationResponse) -> dict[str, Any]:
    source = _normalize(response.cleaned_text)
    keywords = response.brief.source_keywords
    present_keywords = [keyword for keyword in keywords if _normalize(keyword) in source]
    return _check(
        "source_keyword_presence",
        bool(keywords) and bool(present_keywords),
        "No source keyword was grounded in the cleaned transcript.",
    )


def _content_for_concepts(response: ContentGenerationResponse) -> str:
    values = [
        *response.brief.source_keywords,
        *response.brief.key_takeaways,
        response.brief.summary,
        response.brief.core_message,
        *response.assets.youtube_titles,
        response.assets.youtube_description,
        *response.assets.short_hooks,
        response.assets.project_summary,
    ]
    return _normalize("\n".join(values))


def _content_for_claims(response: ContentGenerationResponse) -> str:
    values = [
        *response.assets.youtube_titles,
        response.assets.youtube_description,
        response.assets.linkedin_post,
        *response.assets.short_hooks,
        *response.assets.short_form_concepts,
        *response.assets.portfolio_notes,
        response.assets.project_summary,
        response.brief.summary,
        response.brief.core_message,
    ]
    return "\n".join(values)


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _check(name: str, passed: bool, reason: str) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "reason": "" if passed else reason,
    }


if __name__ == "__main__":
    raise SystemExit(main())
