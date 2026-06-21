from backend.services.transcript_service import clean_transcript


def test_repeated_spaces_are_collapsed() -> None:
    result = clean_transcript("Speaker 1:  Hello    world.")

    assert result.cleaned_text == "Speaker 1: Hello world."


def test_tabs_are_normalized() -> None:
    result = clean_transcript("Speaker 1:\tHello\tworld.")

    assert result.cleaned_text == "Speaker 1: Hello world."


def test_blank_lines_are_removed() -> None:
    result = clean_transcript("Line one\n\n   \nLine two")

    assert result.cleaned_text == "Line one\nLine two"


def test_windows_line_endings_are_normalized() -> None:
    result = clean_transcript("Line one\r\nLine two\rLine three")

    assert result.cleaned_text == "Line one\nLine two\nLine three"


def test_timestamps_and_speaker_labels_are_preserved() -> None:
    text = "[00:01:02] Host:  Welcome back.\n[00:01:05] Guest: Thanks."

    result = clean_transcript(text)

    assert result.cleaned_text == "[00:01:02] Host: Welcome back.\n[00:01:05] Guest: Thanks."


def test_metadata_is_calculated_correctly() -> None:
    text = "  Host:  Hello world.\n\nGuest: Hi.  "

    result = clean_transcript(text)

    assert result.cleaned_text == "Host: Hello world.\nGuest: Hi."
    assert result.metadata.original_character_count == len(text)
    assert result.metadata.cleaned_character_count == len(result.cleaned_text)
    assert result.metadata.word_count == 5
    assert result.metadata.line_count == 2
    assert result.metadata.changed is True


def test_already_clean_text_reports_unchanged() -> None:
    text = "Host: Hello world.\nGuest: Hi."

    result = clean_transcript(text)

    assert result.cleaned_text == text
    assert result.metadata.changed is False
