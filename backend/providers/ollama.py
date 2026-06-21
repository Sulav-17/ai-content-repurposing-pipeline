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
from backend.schemas.content import ContentBrief


PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "prompts" / "content_brief.txt"


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
