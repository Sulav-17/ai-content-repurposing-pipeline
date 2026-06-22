import re
from typing import Any

import streamlit as st

from frontend.api_client import unwrap_saved_response, validate_generation_response


def make_markdown_filename(project_name: str) -> str:
    normalized = project_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    if not normalized:
        return "content-export.md"
    return f"{normalized}.md"


def calculate_offset(
    current_offset: int,
    direction: int,
    page_size: int,
    total: int,
) -> int:
    next_offset = current_offset + (direction * page_size)
    max_offset = max(total - 1, 0)
    if next_offset > max_offset:
        next_offset = (max_offset // page_size) * page_size
    return max(next_offset, 0)


def has_next_page(offset: int, limit: int, total: int) -> bool:
    return offset + limit < total


def unwrap_result(result: dict[str, Any]) -> dict[str, Any]:
    if "generation" in result:
        return unwrap_saved_response(result)
    return validate_generation_response(result)


def chapter_lines(chapters: list[dict[str, Any]]) -> list[str]:
    if not chapters:
        return ["No timestamped chapters were available."]
    return [
        f"{chapter.get('timestamp', '')} - {chapter.get('title', '')}".strip()
        for chapter in chapters
    ]


def render_generation_result(result: dict[str, Any]) -> None:
    generation = unwrap_result(result)
    saved_id = result.get("id")
    created_at = result.get("created_at")
    assets = generation["assets"]
    brief = generation["brief"]

    st.subheader(generation["project_name"])
    st.caption(f"Provider: {generation['provider']}")
    if saved_id:
        st.caption(f"Saved ID: {saved_id}")
    if created_at:
        st.caption(f"Created at: {created_at}")

    st.markdown("## Project Summary")
    st.write(assets["project_summary"])

    with st.expander("Content Brief", expanded=True):
        st.write(brief["summary"])
        st.markdown(f"**Core message:** {brief['core_message']}")
        st.markdown(f"**Target audience:** {brief['target_audience']}")
        st.markdown(f"**Suggested tone:** {brief['suggested_tone']}")
        st.markdown("**Key takeaways:**")
        for takeaway in brief["key_takeaways"]:
            st.markdown(f"- {takeaway}")
        st.markdown("**Source keywords:**")
        st.write(", ".join(brief.get("source_keywords", [])) or "None")

    with st.expander("YouTube Assets", expanded=True):
        st.markdown("**Titles:**")
        for index, title in enumerate(assets["youtube_titles"], start=1):
            st.markdown(f"{index}. {title}")
        st.markdown("**Description:**")
        st.text_area(
            "YouTube Description",
            assets["youtube_description"],
            height=160,
            key=f"youtube_description_{saved_id or 'latest'}",
        )
        st.markdown("**Chapters:**")
        for line in chapter_lines(assets.get("youtube_chapters", [])):
            st.markdown(f"- {line}")

    with st.expander("Social And Portfolio Assets", expanded=True):
        st.markdown("**LinkedIn post:**")
        st.text_area(
            "LinkedIn Post",
            assets["linkedin_post"],
            height=180,
            key=f"linkedin_post_{saved_id or 'latest'}",
        )
        st.markdown("**Short-form hooks:**")
        for index, hook in enumerate(assets["short_hooks"], start=1):
            st.markdown(f"{index}. {hook}")
        st.markdown("**Short-form video concepts:**")
        for concept in assets["short_form_concepts"]:
            st.markdown(f"- {concept}")
        st.markdown("**Portfolio notes:**")
        for note in assets["portfolio_notes"]:
            st.markdown(f"- {note}")

    st.markdown("## Markdown Export")
    st.text_area(
        "Markdown Preview",
        generation["markdown_export"],
        height=240,
        key=f"markdown_preview_{saved_id or 'latest'}",
    )
    st.download_button(
        "Download Markdown",
        generation["markdown_export"],
        file_name=make_markdown_filename(generation["project_name"]),
        mime="text/markdown",
        key=f"download_{saved_id or 'latest'}",
    )

    with st.expander("Debug JSON"):
        st.json(result)


def render_media_job_status(job: dict[str, Any]) -> None:
    st.markdown(f"**Job ID:** `{job['job_id']}`")
    st.write(f"Status: {job['status']}")
    st.write(f"Stage: {job['stage']}")
    st.progress(job.get("progress", 0))

    if job.get("error"):
        st.error(job["error"])

    transcription = job.get("transcription")
    if transcription:
        with st.expander("Transcript", expanded=True):
            st.text_area(
                "Transcript",
                transcription.get("text", ""),
                height=220,
                key=f"media_transcript_{job['job_id']}",
            )

    if job.get("saved_generation_id"):
        st.caption(f"Saved generation ID: {job['saved_generation_id']}")

    if job.get("generation"):
        render_generation_result(job["generation"])
