from streamlit.testing.v1 import AppTest


def test_streamlit_app_has_media_jobs_tab_and_controls(monkeypatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "0.1")

    app = AppTest.from_file("frontend/app.py")
    app.run(timeout=10)

    assert not app.exception
    assert "Media Jobs" in [tab.label for tab in app.tabs]
    assert any(widget.label == "Media project name" for widget in app.text_input)
    assert any(widget.label == "Media provider" for widget in app.selectbox)
    assert any(button.label == "Submit Media Job" for button in app.button)
