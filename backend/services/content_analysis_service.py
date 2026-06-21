from collections import Counter
from dataclasses import dataclass
import re

from backend.schemas.transcript import TranscriptMetadata
from backend.services.transcript_service import clean_transcript


# Common English function words excluded from keyword and sentence scoring.
# Domain words such as api, ai, fastapi, python, content, and automation stay eligible.
STOP_WORDS = frozenset(
    {
        "a",
        "about",
        "after",
        "all",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "can",
        "do",
        "for",
        "from",
        "had",
        "has",
        "have",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "there",
        "this",
        "to",
        "was",
        "we",
        "were",
        "with",
        "you",
        "your",
    }
)

SENTENCE_PATTERN = re.compile(r"[^.!?\n]+[.!?]+|[^.!?\n]+")
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")
TIMESTAMP_PATTERN = re.compile(r"\[?\d{1,2}:\d{2}(?::\d{2})?\]?")


@dataclass(frozen=True)
class KeywordFrequencyResult:
    term: str
    count: int


@dataclass(frozen=True)
class TranscriptAnalysisResult:
    cleaned_text: str
    metadata: TranscriptMetadata
    sentence_count: int
    unique_word_count: int
    top_keywords: list[KeywordFrequencyResult]
    key_points: list[str]


@dataclass(frozen=True)
class SentenceCandidate:
    text: str
    position: int
    tokens: list[str]
    score: float


def analyze_transcript(text: str) -> TranscriptAnalysisResult:
    clean_result = clean_transcript(text)
    cleaned_text = clean_result.cleaned_text
    sentences = detect_sentences(cleaned_text)
    sentence_tokens = [tokenize_meaningful_words(sentence) for sentence in sentences]
    all_tokens = [token for tokens in sentence_tokens for token in tokens]
    token_counts = Counter(all_tokens)

    top_keywords = [
        KeywordFrequencyResult(term=term, count=count)
        for term, count in sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    candidates = [
        SentenceCandidate(
            text=sentence,
            position=index,
            tokens=tokens,
            score=score_sentence(tokens, token_counts),
        )
        for index, (sentence, tokens) in enumerate(zip(sentences, sentence_tokens))
    ]

    return TranscriptAnalysisResult(
        cleaned_text=cleaned_text,
        metadata=clean_result.metadata,
        sentence_count=len(sentences),
        unique_word_count=len(token_counts),
        top_keywords=top_keywords,
        key_points=select_key_points(candidates),
    )


def detect_sentences(cleaned_text: str) -> list[str]:
    sentences: list[str] = []
    for line in cleaned_text.split("\n"):
        for match in SENTENCE_PATTERN.finditer(line):
            sentence = match.group(0).strip()
            if sentence:
                sentences.append(sentence)
    return sentences


def tokenize_meaningful_words(text: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.finditer(text):
        raw_token = match.group(0)
        token = raw_token.lower()
        if token in STOP_WORDS:
            continue
        if token.isnumeric():
            continue
        if TIMESTAMP_PATTERN.fullmatch(raw_token):
            continue
        tokens.append(token)
    return tokens


def score_sentence(tokens: list[str], token_counts: Counter[str]) -> float:
    if not tokens:
        return 0.0
    return sum(token_counts[token] for token in tokens) / len(tokens)


def select_key_points(candidates: list[SentenceCandidate]) -> list[str]:
    first_occurrences: dict[str, SentenceCandidate] = {}
    for candidate in candidates:
        if candidate.text not in first_occurrences:
            first_occurrences[candidate.text] = candidate

    unique_candidates = list(first_occurrences.values())
    positive_candidates = [candidate for candidate in unique_candidates if candidate.score > 0]
    zero_candidates = [candidate for candidate in unique_candidates if candidate.score == 0]

    selected = sorted(
        positive_candidates,
        key=lambda candidate: (-candidate.score, candidate.position),
    )[:5]

    if len(selected) < 5:
        selected.extend(
            sorted(
                zero_candidates,
                key=lambda candidate: candidate.position,
            )[: 5 - len(selected)]
        )

    return [
        candidate.text
        for candidate in sorted(selected, key=lambda candidate: candidate.position)
    ]
