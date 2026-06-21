from backend.schemas.content import ContentBrief
from backend.schemas.generation import PlatformContentAssets, YouTubeChapter
from backend.services.markdown_export_service import generate_markdown_export


def make_brief() -> ContentBrief:
    return ContentBrief(
        summary="Brief summary.",
        core_message="Core message.",
        target_audience="General audience.",
        key_takeaways=["Takeaway one."],
        suggested_tone="Clear.",
        source_keywords=["python", "api"],
    )


def make_assets(chapters=None) -> PlatformContentAssets:
    return PlatformContentAssets(
        youtube_titles=["Title 1", "Title 2", "Title 3", "Title 4", "Title 5"],
        youtube_description="Line one.\nLine two.",
        youtube_chapters=chapters or [],
        linkedin_post="Post line one.\nPost line two.",
        short_hooks=["Hook 1", "Hook 2", "Hook 3", "Hook 4", "Hook 5"],
        short_form_concepts=["Concept 1", "Concept 2", "Concept 3"],
        portfolio_notes=["Note 1", "Note 2", "Note 3"],
        project_summary="Project summary.",
    )


def test_markdown_export_contains_every_required_section() -> None:
    markdown = generate_markdown_export("Demo", make_brief(), make_assets())

    for section in [
        "# Demo",
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
    ]:
        assert section in markdown


def test_markdown_export_formats_lists() -> None:
    markdown = generate_markdown_export("Demo", make_brief(), make_assets())

    assert "1. Title 1" in markdown
    assert "1. Hook 1" in markdown
    assert "- Concept 1" in markdown
    assert "- Note 1" in markdown
    assert "- python" in markdown


def test_markdown_export_preserves_multiline_content() -> None:
    markdown = generate_markdown_export("Demo", make_brief(), make_assets())

    assert "Line one.\nLine two." in markdown
    assert "Post line one.\nPost line two." in markdown


def test_markdown_export_handles_empty_chapters() -> None:
    markdown = generate_markdown_export("Demo", make_brief(), make_assets())

    assert "No timestamped chapters were available." in markdown


def test_markdown_export_includes_chapters_when_available() -> None:
    markdown = generate_markdown_export(
        "Demo",
        make_brief(),
        make_assets([YouTubeChapter(timestamp="00:05", title="Start")]),
    )

    assert "- 00:05 - Start" in markdown


def test_markdown_export_is_deterministic() -> None:
    assert generate_markdown_export("Demo", make_brief(), make_assets()) == generate_markdown_export(
        "Demo",
        make_brief(),
        make_assets(),
    )
