from typing import Any

import httpx

from frontend.config import FrontendSettings


class ApiUnavailableError(Exception):
    pass


class ApiRequestError(Exception):
    pass


class ApiResponseError(Exception):
    pass


class ApiClient:
    def __init__(
        self,
        settings: FrontendSettings,
        client: httpx.Client | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=settings.api_base_url,
            timeout=settings.api_timeout_seconds,
            transport=transport,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def health_check(self) -> dict[str, Any]:
        return self._request_json("GET", "/health")

    def generate_preview(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self._request_json("POST", "/content/generate", json=request)
        return validate_generation_response(response)

    def generate_and_save(self, request: dict[str, Any]) -> dict[str, Any]:
        response = self._request_json("POST", "/generations", json=request)
        return validate_saved_response(response)

    def list_generations(self, limit: int, offset: int) -> dict[str, Any]:
        response = self._request_json(
            "GET",
            "/generations",
            params={"limit": limit, "offset": offset},
        )
        return validate_history_response(response)

    def get_generation(self, generation_id: str) -> dict[str, Any]:
        response = self._request_json("GET", f"/generations/{generation_id}")
        return validate_saved_response(response)

    def delete_generation(self, generation_id: str) -> None:
        self._request_json(
            "DELETE",
            f"/generations/{generation_id}",
            expect_no_content=True,
        )

    def submit_media_job(
        self,
        file_name: str,
        file_bytes: bytes,
        content_type: str,
        project_name: str,
        provider: str = "deterministic",
        save_result: bool = True,
        language: str | None = None,
    ) -> dict[str, Any]:
        data = {
            "project_name": project_name,
            "provider": provider,
            "save_result": str(save_result).lower(),
        }
        if language:
            data["language"] = language
        files = {"file": (file_name, file_bytes, content_type or "application/octet-stream")}
        response = self._request_json("POST", "/media-jobs", data=data, files=files)
        return validate_media_job_submission_response(response)

    def get_media_job(self, job_id: str) -> dict[str, Any]:
        response = self._request_json("GET", f"/media-jobs/{job_id}")
        return validate_media_job_status_response(response)

    def cancel_media_job(self, job_id: str) -> None:
        self._request_json(
            "DELETE",
            f"/media-jobs/{job_id}",
            expect_no_content=True,
        )

    def _request_json(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        expect_no_content: bool = False,
    ) -> dict[str, Any]:
        try:
            response = self.client.request(
                method,
                path,
                json=json,
                params=params,
                data=data,
                files=files,
            )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            raise ApiUnavailableError("API unavailable or request timed out.") from exc
        except httpx.RequestError as exc:
            raise ApiUnavailableError("API unavailable or request timed out.") from exc

        if expect_no_content and response.status_code == 204:
            return {}

        if response.status_code >= 400:
            raise _error_from_status(response)

        try:
            payload = response.json()
        except ValueError as exc:
            raise ApiResponseError("Malformed API response.") from exc

        if not isinstance(payload, dict):
            raise ApiResponseError("Malformed API response.")

        return payload


def validate_generation_response(payload: dict[str, Any]) -> dict[str, Any]:
    required_keys = {
        "provider",
        "project_name",
        "cleaned_text",
        "metadata",
        "analysis",
        "brief",
        "assets",
        "markdown_export",
    }
    if not required_keys.issubset(payload):
        raise ApiResponseError("Malformed API response.")
    if not isinstance(payload["assets"], dict):
        raise ApiResponseError("Malformed API response.")
    if not isinstance(payload["markdown_export"], str):
        raise ApiResponseError("Malformed API response.")
    return payload


def validate_saved_response(payload: dict[str, Any]) -> dict[str, Any]:
    if not {"id", "created_at", "generation"}.issubset(payload):
        raise ApiResponseError("Malformed API response.")
    if not isinstance(payload["generation"], dict):
        raise ApiResponseError("Malformed API response.")
    validate_generation_response(payload["generation"])
    return payload


def unwrap_saved_response(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_saved_response(payload)["generation"]


def validate_history_response(payload: dict[str, Any]) -> dict[str, Any]:
    if not {"items", "total", "limit", "offset"}.issubset(payload):
        raise ApiResponseError("Malformed API response.")
    if not isinstance(payload["items"], list):
        raise ApiResponseError("Malformed API response.")
    for item in payload["items"]:
        if not isinstance(item, dict):
            raise ApiResponseError("Malformed API response.")
        required_item_keys = {
            "id",
            "project_name",
            "provider",
            "project_summary",
            "created_at",
        }
        if not required_item_keys.issubset(item):
            raise ApiResponseError("Malformed API response.")
        if "markdown_export" in item or "input_text" in item:
            raise ApiResponseError("Malformed API response.")
    return payload


def validate_media_job_submission_response(payload: dict[str, Any]) -> dict[str, Any]:
    required_keys = {"job_id", "status", "stage", "created_at"}
    if not required_keys.issubset(payload):
        raise ApiResponseError("Malformed API response.")
    return payload


def validate_media_job_status_response(payload: dict[str, Any]) -> dict[str, Any]:
    required_keys = {
        "job_id",
        "status",
        "stage",
        "progress",
        "created_at",
        "started_at",
        "finished_at",
        "error",
        "transcription",
        "generation",
        "saved_generation_id",
    }
    if not required_keys.issubset(payload):
        raise ApiResponseError("Malformed API response.")
    if not isinstance(payload["progress"], int):
        raise ApiResponseError("Malformed API response.")
    if payload["generation"] is not None:
        validate_generation_response(payload["generation"])
    return payload


def _error_from_status(response: httpx.Response) -> Exception:
    if response.status_code == 422:
        return ApiRequestError(_validation_message(response))
    if response.status_code == 404:
        return ApiRequestError("Saved generation not found.")
    if response.status_code == 409:
        return ApiRequestError("Request conflicts with the current resource state.")
    if response.status_code == 413:
        return ApiRequestError("Uploaded file is too large.")
    if response.status_code == 502:
        return ApiResponseError("Local provider returned an invalid response.")
    if response.status_code == 503:
        return ApiUnavailableError("Provider, API, or database unavailable.")
    return ApiRequestError("API request failed.")


def _validation_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return "Request validation failed."

    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, list):
        messages = []
        for item in detail[:3]:
            if isinstance(item, dict) and item.get("msg"):
                messages.append(str(item["msg"]))
        if messages:
            return "Request validation failed: " + "; ".join(messages)
    if isinstance(detail, str) and detail:
        return f"Request validation failed: {detail}"
    return "Request validation failed."
