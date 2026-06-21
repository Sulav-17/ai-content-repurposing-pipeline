from dataclasses import dataclass
import re

from backend.schemas.transcript import TranscriptMetadata


@dataclass(frozen=True)
class TranscriptCleanResult:
    cleaned_text: str
    metadata: TranscriptMetadata


def clean_transcript(text: str) -> TranscriptCleanResult:
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_text = normalized_text.replace("\t", " ")

    cleaned_lines: list[str] = []
    for line in normalized_text.split("\n"):
        stripped_line = line.strip()
        collapsed_line = re.sub(r" {2,}", " ", stripped_line)
        if collapsed_line:
            cleaned_lines.append(collapsed_line)

    cleaned_text = "\n".join(cleaned_lines)
    metadata = TranscriptMetadata(
        original_character_count=len(text),
        cleaned_character_count=len(cleaned_text),
        word_count=len(cleaned_text.split()),
        line_count=len(cleaned_lines),
        changed=cleaned_text != text,
    )

    return TranscriptCleanResult(cleaned_text=cleaned_text, metadata=metadata)
