"""HTTP model adapters that return only complete quarantined drafts."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import httpx
from pydantic import SecretStr

from careloop.agent_runtime import ModelDraft, ModelRequest


class ProviderResponseError(ValueError):
    """Raised when a provider response cannot form a complete model draft."""


class HTTPResponsePort(Protocol):
    def raise_for_status(self) -> object: ...

    def json(self) -> object: ...


class AsyncHTTPClientPort(Protocol):
    async def post(self, url: str, **kwargs: Any) -> HTTPResponsePort: ...


def _messages(request: ModelRequest) -> list[dict[str, str]]:
    turns = (*request.context_turns, request.input_turn)
    return [{"role": turn.role, "content": turn.text} for turn in turns]


def _draft_id(request: ModelRequest, provider_id: str, model: str, text: str) -> str:
    payload = json.dumps(
        {
            "model": model,
            "provider_id": provider_id,
            "request_id": request.request_id,
            "text": text,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"draft:sha256:{hashlib.sha256(payload).hexdigest()}"


def _mapping(value: object, *, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ProviderResponseError(f"provider response {field} must be an object")
    return value


def _complete_text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderResponseError("provider response content must be non-blank text")
    return value


class OpenAICompatibleModelAdapter:
    """Shared complete-response adapter for DeepSeek and OpenAI-compatible vLLM."""

    def __init__(
        self,
        *,
        provider_id: str,
        model_name: str,
        base_url: str,
        api_key: SecretStr,
        client: AsyncHTTPClientPort | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not provider_id.strip() or not model_name.strip() or not base_url.strip():
            raise ValueError("provider_id, model_name, and base_url must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._provider_id = provider_id
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def generate(self, request: ModelRequest) -> ModelDraft:
        payload: dict[str, object] = {
            "model": self._model_name,
            "messages": _messages(request),
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        raw = await self._post(
            f"{self._base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        body = _mapping(raw, field="root")
        choices = body.get("choices")
        if (
            not isinstance(choices, Sequence)
            or isinstance(choices, (str, bytes))
            or not choices
        ):
            raise ProviderResponseError("provider response choices must be non-empty")
        choice = _mapping(choices[0], field="choices[0]")
        message = _mapping(choice.get("message"), field="message")
        text = _complete_text(message.get("content"))
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=_draft_id(
                request,
                self._provider_id,
                self._model_name,
                text,
            ),
            text=text,
            provider_id=self._provider_id,
            model_name=self._model_name,
        )

    async def _post(self, url: str, **kwargs: Any) -> object:
        if self._client is not None:
            response = await self._client.post(
                url,
                timeout=self._timeout_seconds,
                **kwargs,
            )
            response.raise_for_status()
            return response.json()
        async with httpx.AsyncClient() as client:
            httpx_response = await client.post(
                url,
                timeout=self._timeout_seconds,
                **kwargs,
            )
            httpx_response.raise_for_status()
            return httpx_response.json()


class DeepSeekModelAdapter(OpenAICompatibleModelAdapter):
    """DeepSeek adapter over its OpenAI-compatible chat endpoint."""


class VLLMModelAdapter(OpenAICompatibleModelAdapter):
    """Local vLLM adapter over its OpenAI-compatible chat endpoint."""


class OllamaModelAdapter:
    """Local Ollama adapter over `/api/chat`, with streaming disabled."""

    def __init__(
        self,
        *,
        provider_id: str,
        model_name: str,
        base_url: str,
        client: AsyncHTTPClientPort | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not provider_id.strip() or not model_name.strip() or not base_url.strip():
            raise ValueError("provider_id, model_name, and base_url must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._provider_id = provider_id
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._client = client
        self._timeout_seconds = timeout_seconds

    async def generate(self, request: ModelRequest) -> ModelDraft:
        payload: dict[str, object] = {
            "model": self._model_name,
            "messages": _messages(request),
            "stream": False,
        }
        url = f"{self._base_url}/api/chat"
        if self._client is not None:
            response = await self._client.post(
                url,
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            raw = response.json()
        else:
            async with httpx.AsyncClient() as client:
                httpx_response = await client.post(
                    url,
                    json=payload,
                    timeout=self._timeout_seconds,
                )
                httpx_response.raise_for_status()
                raw = httpx_response.json()
        body = _mapping(raw, field="root")
        message = _mapping(body.get("message"), field="message")
        text = _complete_text(message.get("content"))
        return ModelDraft(
            contract_version="v1",
            request_id=request.request_id,
            draft_id=_draft_id(
                request,
                self._provider_id,
                self._model_name,
                text,
            ),
            text=text,
            provider_id=self._provider_id,
            model_name=self._model_name,
        )
