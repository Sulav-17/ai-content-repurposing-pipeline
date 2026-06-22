import json
import sys
import time
import urllib.error
import urllib.request


API_BASE_URL = "http://127.0.0.1:8000"
FRONTEND_HEALTH_URL = "http://127.0.0.1:8501/_stcore/health"
TIMEOUT_SECONDS = 90


def main() -> int:
    try:
        wait_for_api_ready()
        generation = post_json(
            f"{API_BASE_URL}/content/generate",
            {
                "project_name": "Compose Smoke Test",
                "text": "Host: Local deterministic generation validates the Docker stack.",
                "provider": "deterministic",
            },
        )
        validate_generation(generation)

        saved = post_json(
            f"{API_BASE_URL}/generations",
            {
                "project_name": "Compose Smoke Test",
                "text": "Host: Local deterministic generation validates saved history.",
                "provider": "deterministic",
            },
        )
        generation_id = saved["id"]

        history = get_json(f"{API_BASE_URL}/generations?limit=20&offset=0")
        if not any(item.get("id") == generation_id for item in history.get("items", [])):
            raise RuntimeError("Saved generation was not found in history.")

        retrieved = get_json(f"{API_BASE_URL}/generations/{generation_id}")
        validate_generation(retrieved["generation"])

        delete(f"{API_BASE_URL}/generations/{generation_id}")
        if get_status(f"{API_BASE_URL}/generations/{generation_id}") != 404:
            raise RuntimeError("Deleted generation did not return 404.")

        wait_for_frontend()
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1

    print("Core Compose smoke test passed.")
    return 0


def wait_for_api_ready() -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            payload = get_json(f"{API_BASE_URL}/health/ready")
            if payload.get("status") == "ready":
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("API readiness endpoint did not become ready.")


def wait_for_frontend() -> None:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if get_status(FRONTEND_HEALTH_URL) == 200:
            return
        time.sleep(2)
    raise RuntimeError("Streamlit health endpoint did not respond.")


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def delete(url: str) -> None:
    request = urllib.request.Request(url, method="DELETE")
    with urllib.request.urlopen(request, timeout=10):
        return


def get_status(url: str) -> int:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except (urllib.error.URLError, ConnectionError, OSError, TimeoutError):
        return 0


def validate_generation(payload: dict) -> None:
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
        raise RuntimeError("Generation response was missing required fields.")
    assets = payload.get("assets")
    if not isinstance(assets, dict):
        raise RuntimeError("Generation assets were malformed.")
    if len(assets.get("youtube_titles", [])) != 5:
        raise RuntimeError("Generation response did not include five YouTube titles.")
    if not payload.get("markdown_export"):
        raise RuntimeError("Generation response did not include Markdown export.")


if __name__ == "__main__":
    raise SystemExit(main())
