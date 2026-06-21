from backend.schemas.content import ContentBrief


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
