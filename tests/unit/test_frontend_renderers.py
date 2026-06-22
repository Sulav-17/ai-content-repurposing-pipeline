import pytest

from frontend.api_client import ApiResponseError
from frontend.renderers import (
    calculate_offset,
    chapter_lines,
    has_next_page,
    make_markdown_filename,
    unwrap_result,
)


def generation_payload() -> dict:
    return {
        "provider": "deterministic",
        "project_name": "Demo Project",
        "cleaned_text": "Cleaned",
        "metadata": {},
        "analysis": {},
        "brief": {},
        "assets": {},
        "markdown_export": "# Demo",
    }


def test_safe_markdown_filename_generation() -> None:
    assert make_markdown_filename("AI Content Repurposing Pipeline") == "ai-content-repurposing-pipeline.md"
    assert make_markdown_filename("Local/Content: Pipeline!") == "local-content-pipeline.md"
    assert make_markdown_filename("   ") == "content-export.md"


def test_pagination_helpers() -> None:
    assert calculate_offset(0, -1, 10, 50) == 0
    assert calculate_offset(0, 1, 10, 25) == 10
    assert calculate_offset(20, 1, 10, 25) == 20
    assert has_next_page(10, 10, 25) is True
    assert has_next_page(20, 10, 25) is False


def test_saved_response_unwrapping() -> None:
    saved = {
        "id": "abc",
        "created_at": "2026-01-01T00:00:00Z",
        "generation": generation_payload(),
    }

    assert unwrap_result(saved)["project_name"] == "Demo Project"
    assert unwrap_result(generation_payload())["project_name"] == "Demo Project"


def test_saved_response_unwrapping_rejects_malformed_response() -> None:
    with pytest.raises(ApiResponseError):
        unwrap_result({"generation": {"missing": "fields"}})


def test_empty_chapter_handling() -> None:
    assert chapter_lines([]) == ["No timestamped chapters were available."]
    assert chapter_lines([{"timestamp": "00:05", "title": "Start"}]) == ["00:05 - Start"]
