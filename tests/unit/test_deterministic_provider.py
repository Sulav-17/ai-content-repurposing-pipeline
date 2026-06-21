import httpx

from backend.providers.deterministic import DeterministicContentBriefProvider
from backend.schemas.content import ContentBrief


def test_deterministic_provider_returns_stable_output() -> None:
    provider = DeterministicContentBriefProvider()

    first_result = provider.generate_brief(
        cleaned_text="Host: Python API wins.",
        keywords=["python", "api"],
        key_points=["Host: Python API wins."],
    )
    second_result = provider.generate_brief(
        cleaned_text="Host: Python API wins.",
        keywords=["python", "api"],
        key_points=["Host: Python API wins."],
    )

    assert first_result == second_result


def test_deterministic_provider_returns_valid_content_brief() -> None:
    result = DeterministicContentBriefProvider().generate_brief(
        cleaned_text="Host: Python API wins.",
        keywords=["python", "api"],
        key_points=["Host: Python API wins."],
    )

    assert isinstance(result, ContentBrief)
    assert result.summary
    assert result.core_message
    assert result.target_audience == "General audience (deterministic default)"
    assert result.suggested_tone == "Clear and practical (deterministic default)"


def test_deterministic_provider_preserves_source_keywords() -> None:
    keywords = ["python", "api", "content"]

    result = DeterministicContentBriefProvider().generate_brief(
        cleaned_text="Host: Python API content.",
        keywords=keywords,
        key_points=["Host: Python API content."],
    )

    assert result.source_keywords == keywords


def test_deterministic_provider_limits_takeaways_to_five() -> None:
    key_points = [
        "One.",
        "Two.",
        "Three.",
        "Four.",
        "Five.",
        "Six.",
    ]

    result = DeterministicContentBriefProvider().generate_brief(
        cleaned_text=" ".join(key_points),
        keywords=[],
        key_points=key_points,
    )

    assert result.key_takeaways == key_points[:5]


def test_deterministic_provider_does_not_use_network(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("network should not be used")

    monkeypatch.setattr(httpx, "post", fail_if_called)

    result = DeterministicContentBriefProvider().generate_brief(
        cleaned_text="Host: Local content.",
        keywords=["local"],
        key_points=["Host: Local content."],
    )

    assert result.summary == "Grounded brief based on the transcript: Host: Local content."


def test_deterministic_provider_handles_one_key_point() -> None:
    result = DeterministicContentBriefProvider().generate_brief(
        cleaned_text="Only one point.",
        keywords=["point"],
        key_points=["Only one point."],
    )

    assert result.key_takeaways == ["Only one point."]


def test_deterministic_provider_handles_empty_keywords() -> None:
    result = DeterministicContentBriefProvider().generate_brief(
        cleaned_text="The and or.",
        keywords=[],
        key_points=["The and or."],
    )

    assert result.source_keywords == []
    assert result.key_takeaways == ["The and or."]
