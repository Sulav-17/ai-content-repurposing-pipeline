from backend.services.content_analysis_service import (
    analyze_transcript,
    detect_sentences,
    tokenize_meaningful_words,
)


def keyword_terms(result) -> list[str]:
    return [keyword.term for keyword in result.top_keywords]


def test_punctuation_based_sentence_detection_preserves_punctuation() -> None:
    sentences = detect_sentences("Host: Build APIs. Guest: Why? Host: Now!")

    assert sentences == ["Host: Build APIs.", "Guest: Why?", "Host: Now!"]


def test_line_based_sentence_detection_preserves_order() -> None:
    sentences = detect_sentences("Host: First line\nGuest: Second line")

    assert sentences == ["Host: First line", "Guest: Second line"]


def test_stop_words_numeric_tokens_and_timestamp_fragments_are_excluded() -> None:
    result = analyze_transcript("[00:00] Host: The API and AI are ready in 2026.")

    terms = keyword_terms(result)
    assert "the" not in terms
    assert "and" not in terms
    assert "are" not in terms
    assert "in" not in terms
    assert "2026" not in terms
    assert "00" not in terms
    assert "api" in terms
    assert "ai" in terms


def test_tokenization_preserves_apostrophes_and_hyphenated_terms() -> None:
    tokens = tokenize_meaningful_words("Don't skip local-first content.")

    assert "don't" in tokens
    assert "local-first" in tokens


def test_keyword_frequency_ranking_and_alphabetical_tie_breaking() -> None:
    result = analyze_transcript(
        "Python API python content API automation FastAPI."
    )

    assert [(keyword.term, keyword.count) for keyword in result.top_keywords] == [
        ("api", 2),
        ("python", 2),
        ("automation", 1),
        ("content", 1),
        ("fastapi", 1),
    ]


def test_top_keywords_are_limited_to_ten() -> None:
    result = analyze_transcript(
        "kilo bravo alpha charlie delta echo foxtrot golf hotel india juliet."
    )

    assert len(result.top_keywords) == 10
    assert keyword_terms(result) == [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
    ]


def test_key_points_are_limited_to_five() -> None:
    result = analyze_transcript(
        "Alpha one. Bravo two. Charlie three. Delta four. Echo five. Foxtrot six."
    )

    assert result.key_points == [
        "Alpha one.",
        "Bravo two.",
        "Charlie three.",
        "Delta four.",
        "Echo five.",
    ]


def test_key_points_preserve_verbatim_sentence_wording() -> None:
    result = analyze_transcript("[00:01] Host: Python API wins!")

    assert result.key_points == ["[00:01] Host: Python API wins!"]


def test_key_points_are_returned_in_transcript_order_after_scoring() -> None:
    result = analyze_transcript(
        "Rare opening sentence. Python Python detail. Python API detail."
    )

    assert result.key_points == [
        "Rare opening sentence.",
        "Python Python detail.",
        "Python API detail.",
    ]


def test_duplicate_key_points_are_prevented_with_first_occurrence_preserved() -> None:
    result = analyze_transcript("Alpha beta. Alpha beta. Gamma beta.")

    assert result.sentence_count == 3
    assert result.key_points == ["Alpha beta.", "Gamma beta."]


def test_zero_score_sentences_are_used_only_after_positive_score_sentences() -> None:
    result = analyze_transcript("The and. Python API. But or.")

    assert result.key_points == ["The and.", "Python API.", "But or."]


def test_repeated_analysis_is_deterministic() -> None:
    text = "Python API wins. Content automation works."

    assert analyze_transcript(text) == analyze_transcript(text)


def test_one_sentence_transcript_is_supported() -> None:
    result = analyze_transcript("Host: One useful sentence.")

    assert result.sentence_count == 1
    assert result.key_points == ["Host: One useful sentence."]


def test_mostly_stop_word_transcript_returns_zero_score_key_points() -> None:
    result = analyze_transcript("The and or. But to of.")

    assert result.sentence_count == 2
    assert result.unique_word_count == 0
    assert result.top_keywords == []
    assert result.key_points == ["The and or.", "But to of."]
