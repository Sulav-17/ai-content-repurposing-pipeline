from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_clean_transcript_returns_200_for_valid_request() -> None:
    response = client.post("/transcripts/clean", json={"text": "Host: Hello"})

    assert response.status_code == 200


def test_clean_transcript_returns_expected_content() -> None:
    text = "  [00:00] Host:\tHello   world.\r\n\r\nGuest:  Hi.  "

    response = client.post("/transcripts/clean", json={"text": text})

    assert response.status_code == 200
    assert response.json() == {
        "cleaned_text": "[00:00] Host: Hello world.\nGuest: Hi.",
        "metadata": {
            "original_character_count": len(text),
            "cleaned_character_count": len("[00:00] Host: Hello world.\nGuest: Hi."),
            "word_count": 6,
            "line_count": 2,
            "changed": True,
        },
    }


def test_clean_transcript_returns_422_for_whitespace_only_input() -> None:
    response = client.post("/transcripts/clean", json={"text": " \n\t "})

    assert response.status_code == 422


def test_clean_transcript_returns_422_for_missing_text() -> None:
    response = client.post("/transcripts/clean", json={})

    assert response.status_code == 422


def test_clean_transcript_returns_422_for_oversized_input() -> None:
    response = client.post("/transcripts/clean", json={"text": "a" * 200_001})

    assert response.status_code == 422
