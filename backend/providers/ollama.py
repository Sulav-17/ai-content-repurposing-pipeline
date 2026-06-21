import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from backend.core.config import Settings
from backend.providers.base import (
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderUnavailableError,
)
from backend.schemas.analysis import TranscriptAnalysis
from backend.schemas.content import ContentBrief
from backend.schemas.generation import PlatformContentAssets


PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "content_brief.txt"
ASSET_PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "content_assets.txt"


class OllamaContentBriefProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_brief(
        self,
        cleaned_text: str,
        keywords: list[str],
        key_points: list[str],
    ) -> ContentBrief:
        if not self.settings.ollama_model.strip():
            raise ProviderConfigurationError("OLLAMA_MODEL must be set to use the Ollama provider.")

        prompt = self._build_prompt(cleaned_text, keywords, key_points)
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }

        try:
            response = httpx.post(
                f"{self.settings.ollama_base_url}/api/generate",
                json=payload,
                timeout=self.settings.ollama_timeout_seconds,
            )
            if response.status_code >= 400:
                raise ProviderUnavailableError("Ollama returned an unavailable status.")
        except httpx.TimeoutException as exc:
            raise ProviderUnavailableError("Ollama request timed out.") from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError("Ollama is unavailable.") from exc

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError("Ollama returned a malformed JSON payload.") from exc

        generated_content = response_payload.get("response")
        if not isinstance(generated_content, str):
            raise ProviderResponseError("Ollama response payload is missing a string response field.")

        try:
            brief_payload = json.loads(generated_content)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("Ollama generated invalid JSON.") from exc

        try:
            return ContentBrief.model_validate(brief_payload)
        except ValidationError as exc:
            raise ProviderResponseError("Ollama generated an invalid content brief schema.") from exc

    def _build_prompt(
        self,
        cleaned_text: str,
        keywords: list[str],
        key_points: list[str],
    ) -> str:
        template = PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        return template.format(
            cleaned_text=cleaned_text,
            keywords=json.dumps(keywords, ensure_ascii=True),
            key_points=json.dumps(key_points, ensure_ascii=True),
        )


class OllamaPlatformContentProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_assets(
        self,
        project_name: str,
        cleaned_text: str,
        analysis: TranscriptAnalysis,
        brief: ContentBrief,
        allowed_timestamps: list[str],
    ) -> PlatformContentAssets:
        if not self.settings.ollama_model.strip():
            raise ProviderConfigurationError("OLLAMA_MODEL must be set to use the Ollama provider.")

        prompt = self._build_prompt(
            project_name=project_name,
            cleaned_text=cleaned_text,
            analysis=analysis,
            brief=brief,
            allowed_timestamps=allowed_timestamps,
        )
        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        response_payload = _post_to_ollama(self.settings, payload)
        generated_content = response_payload.get("response")
        if not isinstance(generated_content, str):
            raise ProviderResponseError("Ollama response payload is missing a string response field.")

        try:
            assets_payload = json.loads(generated_content)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("Ollama generated invalid JSON.") from exc

        try:
            assets = PlatformContentAssets.model_validate(assets_payload)
        except ValidationError as exc:
            raise ProviderResponseError("Ollama generated an invalid platform content schema.") from exc

        allowed_timestamp_set = set(allowed_timestamps)
        if not allowed_timestamps and assets.youtube_chapters:
            raise ProviderResponseError("Ollama generated chapters when no source timestamps were available.")

        for chapter in assets.youtube_chapters:
            if chapter.timestamp not in allowed_timestamp_set:
                raise ProviderResponseError("Ollama generated a fabricated chapter timestamp.")

        return assets

    def _build_prompt(
        self,
        project_name: str,
        cleaned_text: str,
        analysis: TranscriptAnalysis,
        brief: ContentBrief,
        allowed_timestamps: list[str],
    ) -> str:
        template = ASSET_PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
        return template.format(
            project_name=project_name,
            cleaned_text=cleaned_text,
            analysis=analysis.model_dump_json(),
            brief=brief.model_dump_json(),
            allowed_timestamps=json.dumps(allowed_timestamps, ensure_ascii=True),
        )


def _post_to_ollama(settings: Settings, payload: dict[str, object]) -> dict[str, object]:
    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json=payload,
            timeout=settings.ollama_timeout_seconds,
        )
        if response.status_code >= 400:
            raise ProviderUnavailableError("Ollama returned an unavailable status.")
    except httpx.TimeoutException as exc:
        raise ProviderUnavailableError("Ollama request timed out.") from exc
    except httpx.RequestError as exc:
        raise ProviderUnavailableError("Ollama is unavailable.") from exc

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise ProviderResponseError("Ollama returned a malformed JSON payload.") from exc

    return response_payload
