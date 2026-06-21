from backend.schemas.analysis import KeywordFrequency, TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import PlatformContentAssets
from backend.providers.deterministic import DeterministicPlatformContentProvider


def make_analysis() -> TranscriptAnalysis:
    return TranscriptAnalysis(
        sentence_count=2,
        unique_word_count=4,
        top_keywords=[
            KeywordFrequency(term="python", count=2),
            KeywordFrequency(term="api", count=1),
        ],
        key_points=[
            "Host: Python API wins.",
            "Guest: Python content works.",
        ],
    )


def make_brief() -> ContentBrief:
    return ContentBrief(
        summary="Python API source summary.",
        core_message="Python API wins.",
        target_audience="General audience.",
        key_takeaways=[
            "Host: Python API wins.",
            "Guest: Python content works.",
        ],
        suggested_tone="Clear.",
        source_keywords=["python", "api"],
    )


def generate_assets(
    cleaned_text: str = "Host: Python API wins.\nGuest: Python content works.",
    allowed_timestamps: list[str] | None = None,
) -> PlatformContentAssets:
    return DeterministicPlatformContentProvider().generate_assets(
        project_name="Demo Project",
        cleaned_text=cleaned_text,
        analysis=make_analysis(),
        brief=make_brief(),
        allowed_timestamps=allowed_timestamps or [],
    )


def test_deterministic_generation_returns_valid_schema() -> None:
    result = generate_assets()

    assert isinstance(result, PlatformContentAssets)
    assert result.youtube_description
    assert result.linkedin_post
    assert result.project_summary


def test_deterministic_generation_is_stable() -> None:
    assert generate_assets() == generate_assets()


def test_deterministic_generation_returns_exactly_five_unique_titles() -> None:
    result = generate_assets()

    assert len(result.youtube_titles) == 5
    assert len({title.casefold() for title in result.youtube_titles}) == 5


def test_deterministic_generation_returns_exactly_five_unique_hooks() -> None:
    result = generate_assets()

    assert len(result.short_hooks) == 5
    assert len({hook.casefold() for hook in result.short_hooks}) == 5


def test_deterministic_generation_respects_concept_and_note_limits() -> None:
    result = generate_assets()

    assert 3 <= len(result.short_form_concepts) <= 5
    assert 3 <= len(result.portfolio_notes) <= 8


def test_deterministic_generation_returns_empty_chapters_without_source_timestamps() -> None:
    result = generate_assets()

    assert result.youtube_chapters == []


def test_deterministic_generation_preserves_source_timestamps() -> None:
    result = generate_assets(
        cleaned_text="[00:05] Host: Start here.\n00:10 Guest: Next idea.",
        allowed_timestamps=["00:05", "00:10"],
    )

    assert [chapter.timestamp for chapter in result.youtube_chapters] == [
        "00:05",
        "00:10",
    ]


def test_deterministic_generation_avoids_obvious_fabricated_metrics() -> None:
    result = generate_assets()
    combined_output = " ".join(
        [
            *result.youtube_titles,
            result.youtube_description,
            result.linkedin_post,
            *result.short_hooks,
            *result.short_form_concepts,
            *result.portfolio_notes,
            result.project_summary,
        ]
    ).casefold()

    assert "revenue" not in combined_output
    assert "users" not in combined_output
    assert "time savings" not in combined_output
    assert "performance" not in combined_output


def test_deterministic_generation_handles_sparse_transcript() -> None:
    analysis = TranscriptAnalysis(
        sentence_count=1,
        unique_word_count=0,
        top_keywords=[],
        key_points=["The and or."],
    )
    brief = ContentBrief(
        summary="Sparse source summary.",
        core_message="Sparse source message.",
        target_audience="General audience.",
        key_takeaways=["The and or."],
        suggested_tone="Clear.",
        source_keywords=[],
    )

    result = DeterministicPlatformContentProvider().generate_assets(
        project_name="Sparse Project",
        cleaned_text="The and or.",
        analysis=analysis,
        brief=brief,
        allowed_timestamps=[],
    )

    assert len(result.youtube_titles) == 5
    assert len(result.short_hooks) == 5
    assert result.youtube_chapters == []
