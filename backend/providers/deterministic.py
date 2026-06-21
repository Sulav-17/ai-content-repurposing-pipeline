from backend.schemas.content import ContentBrief
from backend.schemas.analysis import TranscriptAnalysis
from backend.schemas.generation import PlatformContentAssets, YouTubeChapter


class DeterministicContentBriefProvider:
    def generate_brief(
        self,
        cleaned_text: str,
        keywords: list[str],
        key_points: list[str],
    ) -> ContentBrief:
        takeaways = key_points[:5]
        if not takeaways:
            takeaways = [self._fallback_takeaway(cleaned_text)]

        first_point = takeaways[0]
        summary = f"Grounded brief based on the transcript: {first_point}"
        core_message = f"The transcript emphasizes: {first_point}"

        return ContentBrief(
            summary=summary,
            core_message=core_message,
            target_audience="General audience (deterministic default)",
            key_takeaways=takeaways,
            suggested_tone="Clear and practical (deterministic default)",
            source_keywords=keywords[:10],
        )

    def _fallback_takeaway(self, cleaned_text: str) -> str:
        if cleaned_text.strip():
            return cleaned_text.strip()
        return "No key point was available from the transcript."


class DeterministicPlatformContentProvider:
    def generate_assets(
        self,
        project_name: str,
        cleaned_text: str,
        analysis: TranscriptAnalysis,
        brief: ContentBrief,
        allowed_timestamps: list[str],
    ) -> PlatformContentAssets:
        keywords = brief.source_keywords or [
            keyword.term for keyword in analysis.top_keywords
        ]
        keyword_phrase = _join_terms(keywords[:3]) or "the source transcript"
        first_key_point = _first_available(analysis.key_points, brief.key_takeaways)
        chapters = _build_chapters(cleaned_text, allowed_timestamps)

        return PlatformContentAssets(
            youtube_titles=_unique_templates(
                [
                    f"{project_name}: {brief.core_message}",
                    f"What {project_name} Shows About {keyword_phrase}",
                    f"{project_name} Key Takeaways",
                    f"Inside {project_name}: {first_key_point}",
                    f"{project_name} Explained Through Source Highlights",
                ],
                fallback_prefix=project_name,
                limit=5,
            ),
            youtube_description=_build_youtube_description(brief, keywords),
            youtube_chapters=chapters,
            linkedin_post=_build_linkedin_post(project_name, brief),
            short_hooks=_unique_templates(
                [
                    f"Start with this: {first_key_point}",
                    f"{project_name} in one idea: {brief.core_message}",
                    f"A practical look at {keyword_phrase}.",
                    f"Here is what stood out from {project_name}.",
                    f"Use this source-backed takeaway: {first_key_point}",
                ],
                fallback_prefix=f"{project_name} hook",
                limit=5,
            ),
            short_form_concepts=_build_short_form_concepts(project_name, brief),
            portfolio_notes=_build_portfolio_notes(project_name, brief, keywords),
            project_summary=f"{project_name}: {brief.summary}",
        )


def _join_terms(terms: list[str]) -> str:
    return ", ".join(terms)


def _first_available(key_points: list[str], takeaways: list[str]) -> str:
    for value in [*key_points, *takeaways]:
        if value.strip():
            return value.strip()
    return "Source-backed content highlights"


def _unique_templates(values: list[str], fallback_prefix: str, limit: int) -> list[str]:
    unique_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        candidate = _compact(value)
        normalized_candidate = candidate.casefold()
        if candidate and normalized_candidate not in seen_values:
            seen_values.add(normalized_candidate)
            unique_values.append(candidate)
        if len(unique_values) == limit:
            return unique_values

    while len(unique_values) < limit:
        candidate = f"{fallback_prefix} {len(unique_values) + 1}"
        normalized_candidate = candidate.casefold()
        if normalized_candidate not in seen_values:
            seen_values.add(normalized_candidate)
            unique_values.append(candidate)

    return unique_values


def _compact(value: str) -> str:
    return " ".join(value.split())


def _build_youtube_description(
    brief: ContentBrief,
    keywords: list[str],
) -> str:
    lines = [
        brief.summary,
        "",
        f"Core message: {brief.core_message}",
        "",
        "Key takeaways:",
    ]
    lines.extend(f"- {takeaway}" for takeaway in brief.key_takeaways[:5])
    if keywords:
        lines.extend(["", f"Source keywords: {_join_terms(keywords[:10])}"])
    return "\n".join(lines).strip()


def _build_linkedin_post(project_name: str, brief: ContentBrief) -> str:
    lines = [
        f"{project_name}",
        "",
        brief.summary,
        "",
        "Source-backed takeaways:",
    ]
    lines.extend(f"- {takeaway}" for takeaway in brief.key_takeaways[:5])
    lines.extend(["", f"Core message: {brief.core_message}"])
    return "\n".join(lines).strip()


def _build_short_form_concepts(
    project_name: str,
    brief: ContentBrief,
) -> list[str]:
    concepts = [
        f"Open with the core message from {project_name}: {brief.core_message}",
        f"Turn the first takeaway into a direct-to-camera explanation: {brief.key_takeaways[0]}",
        f"Use the brief summary as a concise source-backed explainer: {brief.summary}",
    ]
    if len(brief.key_takeaways) > 1:
        concepts.append(f"Compare two transcript takeaways from {project_name}.")
    if brief.source_keywords:
        concepts.append(f"Define the source keywords in context: {_join_terms(brief.source_keywords[:3])}.")
    return concepts[:5]


def _build_portfolio_notes(
    project_name: str,
    brief: ContentBrief,
    keywords: list[str],
) -> list[str]:
    notes = [
        f"{project_name} includes a source-backed content brief.",
        f"The core message is grounded in the transcript: {brief.core_message}",
        f"Key takeaways were preserved from transcript-derived analysis.",
    ]
    if keywords:
        notes.append(f"Source keywords used for generation: {_join_terms(keywords[:5])}.")
    notes.append("No unsupported quantified claims were added.")
    return notes[:8]


def _build_chapters(
    cleaned_text: str,
    allowed_timestamps: list[str],
) -> list[YouTubeChapter]:
    chapters: list[YouTubeChapter] = []
    for timestamp in allowed_timestamps[:12]:
        title = _chapter_title_for_timestamp(cleaned_text, timestamp)
        chapters.append(YouTubeChapter(timestamp=timestamp, title=title))
    return chapters


def _chapter_title_for_timestamp(cleaned_text: str, timestamp: str) -> str:
    for line in cleaned_text.split("\n"):
        if timestamp in line:
            title = line.replace(f"[{timestamp}]", "").replace(timestamp, "").strip()
            return _compact(title.strip("-: ")) or f"Chapter at {timestamp}"
    return f"Chapter at {timestamp}"
