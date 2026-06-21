from backend.schemas.content import ContentBrief
from backend.schemas.generation import PlatformContentAssets


def generate_markdown_export(
    project_name: str,
    brief: ContentBrief,
    assets: PlatformContentAssets,
) -> str:
    lines = [
        f"# {project_name}",
        "",
        "## Project Summary",
        assets.project_summary,
        "",
        "## Content Brief",
        f"**Summary:** {brief.summary}",
        "",
        f"**Core Message:** {brief.core_message}",
        "",
        f"**Target Audience:** {brief.target_audience}",
        "",
        f"**Suggested Tone:** {brief.suggested_tone}",
        "",
        "## YouTube Titles",
    ]

    lines.extend(_numbered_lines(assets.youtube_titles))
    lines.extend(["", "## YouTube Description", assets.youtube_description, ""])
    lines.append("## YouTube Chapters")
    if assets.youtube_chapters:
        lines.extend(
            f"- {chapter.timestamp} - {chapter.title}"
            for chapter in assets.youtube_chapters
        )
    else:
        lines.append("No timestamped chapters were available.")

    lines.extend(["", "## LinkedIn Post", assets.linkedin_post, ""])
    lines.append("## Short-Form Hooks")
    lines.extend(_numbered_lines(assets.short_hooks))
    lines.extend(["", "## Short-Form Video Concepts"])
    lines.extend(_bullet_lines(assets.short_form_concepts))
    lines.extend(["", "## Portfolio Notes"])
    lines.extend(_bullet_lines(assets.portfolio_notes))
    lines.extend(["", "## Source Keywords"])
    lines.extend(_bullet_lines(brief.source_keywords))

    return "\n".join(lines).strip()


def _numbered_lines(values: list[str]) -> list[str]:
    return [f"{index}. {value}" for index, value in enumerate(values, start=1)]


def _bullet_lines(values: list[str]) -> list[str]:
    if not values:
        return ["- None"]
    return [f"- {value}" for value in values]
