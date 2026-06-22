import importlib
import sys

from streamlit.testing.v1 import AppTest


def test_streamlit_app_loads_without_live_backend(monkeypatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "0.1")

    app = AppTest.from_file("frontend/app.py")
    app.run(timeout=10)

    assert not app.exception
    assert any("Backend unavailable" in element.value for element in app.warning)


def test_streamlit_app_has_main_tabs_and_controls(monkeypatch) -> None:
    monkeypatch.setenv("API_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "0.1")

    app = AppTest.from_file("frontend/app.py")
    app.run(timeout=10)

    tab_labels = [tab.label for tab in app.tabs]
    assert "Generate" in tab_labels
    assert "Saved History" in tab_labels
    assert any(widget.label == "Project name" for widget in app.text_input)
    assert any(widget.label == "Transcript text" for widget in app.text_area)
    assert any(widget.label == "Provider" for widget in app.selectbox)
    assert any(button.label == "Generate Preview" for button in app.button)
    assert any(button.label == "Generate and Save" for button in app.button)


def test_frontend_modules_do_not_import_prohibited_backend_layers() -> None:
    prohibited_prefixes = [
        "backend.database",
        "backend.models",
        "backend.repositories",
        "backend.services",
        "backend.providers",
    ]
    for module_name in list(sys.modules):
        if module_name.startswith("frontend") or any(
            module_name.startswith(prefix) for prefix in prohibited_prefixes
        ):
            sys.modules.pop(module_name, None)

    for module_name in [
        "frontend.config",
        "frontend.api_client",
        "frontend.renderers",
        "frontend.app",
    ]:
        importlib.import_module(module_name)

    imported_modules = set(sys.modules)
    for prefix in prohibited_prefixes:
        assert prefix not in imported_modules
