import argparse
import json
import mimetypes
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API_BASE_URL = "http://127.0.0.1:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an optional media Compose smoke test.")
    parser.add_argument("media_path", help="Path to a local media file to upload.")
    parser.add_argument("--save", action="store_true", help="Persist the completed generation.")
    parser.add_argument("--timeout", type=int, default=600, help="Maximum seconds to wait for completion.")
    args = parser.parse_args()

    media_path = Path(args.media_path)
    if not media_path.is_file():
        print("Media smoke test failed: media file does not exist.", file=sys.stderr)
        return 1

    try:
        submission = submit_job(media_path, save_result=args.save)
        result = wait_for_job(submission["job_id"], args.timeout)
        validate_completed_job(result)
    except Exception as exc:
        print(f"Media smoke test failed: {exc}", file=sys.stderr)
        return 1

    print("Media Compose smoke test passed.")
    return 0


def submit_job(media_path: Path, save_result: bool) -> dict:
    boundary = f"----ai-pipeline-{secrets.token_hex(12)}"
    content_type = mimetypes.guess_type(media_path.name)[0] or "application/octet-stream"
    fields = {
        "project_name": "Compose Media Smoke Test",
        "provider": "deterministic",
        "save_result": "true" if save_result else "false",
    }
    body = multipart_body(boundary, fields, media_path, content_type)
    request = urllib.request.Request(
        f"{API_BASE_URL}/media-jobs",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_job(job_id: str, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        result = get_json(f"{API_BASE_URL}/media-jobs/{urllib.parse.quote(job_id)}")
        print(f"Job {job_id}: {result.get('status')} / {result.get('stage')} / {result.get('progress')}%")
        if result.get("status") in {"finished", "failed", "canceled"}:
            return result
        time.sleep(5)
    raise RuntimeError("Media job did not finish before timeout.")


def validate_completed_job(result: dict) -> None:
    if result.get("status") != "finished":
        raise RuntimeError("Media job did not finish successfully.")
    if result.get("stage") != "complete" or result.get("progress") != 100:
        raise RuntimeError("Media job did not report complete progress.")
    transcription = result.get("transcription") or {}
    if not transcription.get("text"):
        raise RuntimeError("Media job did not produce a transcript.")
    generation = result.get("generation") or {}
    required_generation_keys = {"provider", "project_name", "assets", "markdown_export"}
    if not required_generation_keys.issubset(generation):
        raise RuntimeError("Media job did not produce a valid generation.")


def multipart_body(boundary: str, fields: dict[str, str], media_path: Path, content_type: str) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                f"{value}\r\n".encode("utf-8"),
            ]
        )
    chunks.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="file"; filename="{media_path.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            media_path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return b"".join(chunks)


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"API returned HTTP {exc.code}.") from exc


if __name__ == "__main__":
    raise SystemExit(main())
