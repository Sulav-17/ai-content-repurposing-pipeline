import httpx
import pytest

from frontend.api_client import (
    ApiClient,
    ApiRequestError,
    ApiResponseError,
    ApiUnavailableError,
    validate_history_response,
    validate_saved_response,
)
from frontend.config import FrontendConfigurationError, FrontendSettings, _validate_base_url, _validate_timeout


def settings(base_url: str = "http://api.test") -> FrontendSettings:
    return FrontendSettings(api_base_url=base_url, api_timeout_seconds=5)


def generation_payload() -> dict:
    return {
        "provider": "deterministic",
        "project_name": "Demo",
        "cleaned_text": "Cleaned",
        "metadata": {},
        "analysis": {},
        "brief": {},
        "assets": {},
        "markdown_export": "# Demo",
    }


def saved_payload() -> dict:
    return {
        "id": "abc",
        "created_at": "2026-01-01T00:00:00Z",
        "generation": generation_payload(),
    }


def history_payload() -> dict:
    return {
        "items": [
            {
                "id": "abc",
                "project_name": "Demo",
                "provider": "deterministic",
                "project_summary": "Summary",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
        "total": 1,
        "limit": 10,
        "offset": 0,
    }


def make_client(handler) -> ApiClient:
    transport = httpx.MockTransport(handler)
    return ApiClient(settings("http://api.test/"), transport=transport)


def test_frontend_config_validates_url_and_timeout() -> None:
    assert _validate_base_url("http://127.0.0.1:8000///") == "http://127.0.0.1:8000"
    assert _validate_timeout("2.5") == 2.5
    with pytest.raises(FrontendConfigurationError):
        _validate_base_url("ftp://example.com")
    with pytest.raises(FrontendConfigurationError):
        _validate_base_url("http://user:pass@example.com")
    with pytest.raises(FrontendConfigurationError):
        _validate_timeout("0")


def test_api_client_constructs_urls_and_health_request() -> None:
    seen_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        return httpx.Response(200, json={"status": "ok"})

    client = make_client(handler)

    assert client.health_check() == {"status": "ok"}
    assert seen_urls == ["http://api.test/health"]


def test_api_client_preview_and_save_requests() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/content/generate":
            return httpx.Response(200, json=generation_payload())
        return httpx.Response(201, json=saved_payload())

    client = make_client(handler)

    assert client.generate_preview({"text": "x", "project_name": "Demo"})["project_name"] == "Demo"
    assert client.generate_and_save({"text": "x", "project_name": "Demo"})["id"] == "abc"
    assert seen_paths == ["/content/generate", "/generations"]


def test_api_client_list_get_and_delete_operations() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, str(request.url)))
        if request.method == "GET" and request.url.path == "/generations":
            return httpx.Response(200, json=history_payload())
        if request.method == "GET":
            return httpx.Response(200, json=saved_payload())
        return httpx.Response(204)

    client = make_client(handler)

    assert client.list_generations(10, 20)["offset"] == 0
    assert client.get_generation("abc")["id"] == "abc"
    assert client.delete_generation("abc") is None
    assert seen[0] == ("GET", "http://api.test/generations?limit=10&offset=20")
    assert seen[2] == ("DELETE", "http://api.test/generations/abc")


def test_api_client_handles_timeout_and_connection_failure() -> None:
    timeout_client = make_client(lambda request: (_ for _ in ()).throw(httpx.TimeoutException("secret url")))
    connection_client = make_client(lambda request: (_ for _ in ()).throw(httpx.ConnectError("secret url")))

    with pytest.raises(ApiUnavailableError, match="API unavailable"):
        timeout_client.health_check()
    with pytest.raises(ApiUnavailableError, match="API unavailable"):
        connection_client.health_check()


@pytest.mark.parametrize(
    ("status_code", "payload", "exception_type", "message"),
    [
        (422, {"detail": [{"msg": "Field required"}]}, ApiRequestError, "Field required"),
        (404, {"detail": "missing"}, ApiRequestError, "Saved generation not found"),
        (502, {"detail": "secret backend"}, ApiResponseError, "Local provider returned an invalid response"),
        (503, {"detail": "postgresql://secret"}, ApiUnavailableError, "Provider, API, or database unavailable"),
    ],
)
def test_api_client_maps_status_codes_safely(status_code, payload, exception_type, message) -> None:
    client = make_client(lambda request: httpx.Response(status_code, json=payload))

    with pytest.raises(exception_type) as exc_info:
        client.health_check()

    assert message in str(exc_info.value)
    assert "postgresql://" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)


def test_api_client_handles_malformed_json_and_success_payloads() -> None:
    bad_json_client = make_client(lambda request: httpx.Response(200, content=b"not json"))
    bad_payload_client = make_client(lambda request: httpx.Response(200, json={"missing": "keys"}))

    with pytest.raises(ApiResponseError, match="Malformed API response"):
        bad_json_client.health_check()
    with pytest.raises(ApiResponseError, match="Malformed API response"):
        bad_payload_client.generate_preview({})


def test_frontend_response_validation_helpers_reject_malformed_shapes() -> None:
    with pytest.raises(ApiResponseError):
        validate_saved_response({"id": "abc"})
    with pytest.raises(ApiResponseError):
        validate_history_response({"items": [{"markdown_export": "# bad"}], "total": 1, "limit": 10, "offset": 0})
