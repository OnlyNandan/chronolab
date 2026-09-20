"""
LLM provider abstraction for the lab-extraction pipeline (MIGRATION_PLAN.md Phase 2).

Two implementations, selected by AWS_MODE:
  - OllamaProvider: local Ollama models (vision + text), used when AWS_MODE=local.
  - BedrockProvider: AWS Bedrock via the Converse API, used when AWS_MODE=cloud.

Phase A and Phase B in pipeline.py keep their exact prompts and JSON contracts —
only which model executes the call changes here.
"""
import base64
import json
import logging
import time
from abc import ABC, abstractmethod

import ollama

try:
    from . import config  # imported as backend.providers
except ImportError:
    import config  # run standalone / imported flat (e.g. from pipeline.py)

logger = logging.getLogger("chronolab.providers")


class LLMProvider(ABC):
    @abstractmethod
    def extract_from_image(self, image_b64: str, prompt: str) -> dict:
        """Vision call for Phase A. Returns parsed JSON matching the Phase A schema."""

    @abstractmethod
    def extract_from_text(self, prompt: str) -> dict:
        """Text-only call. Used for Phase A's vision fallback and for Phase B."""

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, history: list = None) -> str:
        """Free-text chat completion (not JSON). Used by the timeline chat assistant
        and Doctor Insights, both of which need prose output rather than a JSON contract."""


class OllamaProvider(LLMProvider):
    def extract_from_image(self, image_b64: str, prompt: str) -> dict:
        response = ollama.chat(
            model=config.OLLAMA_VISION_MODEL,
            messages=[{"role": "user", "content": prompt, "images": [image_b64]}],
            format="json",
            options={"temperature": 0.1},
        )
        return json.loads(response["message"]["content"])

    def extract_from_text(self, prompt: str) -> dict:
        response = ollama.chat(
            model=config.OLLAMA_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.1},
        )
        return json.loads(response["message"]["content"])

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, history: list = None) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history or [])
        messages.append({"role": "user", "content": user_prompt})
        response = ollama.chat(
            model=config.OLLAMA_TEXT_MODEL,
            messages=messages,
            options={"temperature": temperature},
        )
        return response["message"]["content"]


def _bedrock_retry(fn, *args, max_attempts=5, base_delay=1.0, **kwargs):
    """Exponential backoff on Bedrock throttling. Re-raises everything else immediately."""
    from botocore.exceptions import ClientError

    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            if code in ("ThrottlingException", "TooManyRequestsException") and attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    f"Bedrock throttled ({code}), attempt {attempt}/{max_attempts}, "
                    f"retrying in {delay:.1f}s"
                )
                time.sleep(delay)
                continue
            raise


class BedrockProvider(LLMProvider):
    def __init__(self):
        self.client = config.get_boto3_client("bedrock-runtime", region_name=config.BEDROCK_REGION)

    def _converse_json(self, model_id: str, content: list) -> dict:
        response = _bedrock_retry(
            self.client.converse,
            modelId=model_id,
            messages=[{"role": "user", "content": content}],
            inferenceConfig={"temperature": 0.1},
        )
        text = response["output"]["message"]["content"][0]["text"]
        return json.loads(text)

    def extract_from_image(self, image_b64: str, prompt: str) -> dict:
        image_bytes = base64.b64decode(image_b64)
        content = [
            {"text": prompt},
            {"image": {"format": "jpeg", "source": {"bytes": image_bytes}}},
        ]
        return self._converse_json(config.BEDROCK_VISION_MODEL_ID, content)

    def extract_from_text(self, prompt: str) -> dict:
        return self._converse_json(config.BEDROCK_TEXT_MODEL_ID, [{"text": prompt}])

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2, history: list = None) -> str:
        # `history` is the provider-agnostic [{"role", "content": str}] shape used by
        # callers (and by OllamaProvider directly) — Converse needs content as blocks.
        messages = [
            {"role": turn["role"], "content": [{"text": turn["content"]}]}
            for turn in (history or [])
        ]
        messages.append({"role": "user", "content": [{"text": user_prompt}]})
        response = _bedrock_retry(
            self.client.converse,
            modelId=config.BEDROCK_TEXT_MODEL_ID,
            system=[{"text": system_prompt}],
            messages=messages,
            inferenceConfig={"temperature": temperature},
        )
        return response["output"]["message"]["content"][0]["text"]


def get_provider() -> LLMProvider:
    if config.AWS_MODE == "local":
        return OllamaProvider()
    return BedrockProvider()
