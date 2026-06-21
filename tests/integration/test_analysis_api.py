from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_analyze_transcript_returns_expected_response() -> None:
    text = "  [00:00] Host:\tPython   API wins.\r\n\r\nGuest:  Python content works.  "

    response = client.post("/transcripts/analyze", json={"text": text})

    assert response.status_code == 200
    assert response.json() == {
        "cleaned_text": "[00:00] Host: Python API wins.\nGuest: Python content works.",
        "metadata": {
            "original_character_count": len(text),
            "cleaned_character_count": len(
                "[00:00] Host: Python API wins.\nGuest: Python content works."
            ),
            "word_count": 9,
            "line_count": 2,
            "changed": True,
        },
        "analysis": {
            "sentence_count": 2,
            "unique_word_count": 7,
            "top_keywords": [
                {"term": "python", "count": 2},
                {"term": "api", "count": 1},
                {"term": "content", "count": 1},
                {"term": "guest", "count": 1},
                {"term": "host", "count": 1},
                {"term": "wins", "count": 1},
                {"term": "works", "count": 1},
            ],
            "key_points": [
                "[00:00] Host: Python API wins.",
                "Guest: Python content works.",
            ],
        },
    }


def test_analyze_transcript_applies_cleaning_before_analysis() -> None:
    response = client.post(
        "/transcripts/analyze",
        json={"text": "  Host:\tPython   API.\n\nGuest:  Python API.  "},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["cleaned_text"] == "Host: Python API.\nGuest: Python API."
    assert body["metadata"]["changed"] is True
    assert body["analysis"]["sentence_count"] == 2
    assert body["analysis"]["top_keywords"][:2] == [
        {"term": "api", "count": 2},
        {"term": "python", "count": 2},
    ]


def test_analyze_transcript_returns_422_for_whitespace_only_input() -> None:
    response = client.post("/transcripts/analyze", json={"text": " \n\t "})

    assert response.status_code == 422


def test_analyze_transcript_returns_422_for_missing_text() -> None:
    response = client.post("/transcripts/analyze", json={})

    assert response.status_code == 422


def test_analyze_transcript_returns_422_for_oversized_input() -> None:
    response = client.post("/transcripts/analyze", json={"text": "a" * 200_001})

    assert response.status_code == 422
