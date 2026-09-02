import asyncio
from dataclasses import dataclass, field
from typing import Any

import pytest
from pydantic import SecretStr

from careloop.agent_runtime import (
    ModelRequest,
    ModelRuntimeFailureCode,
    PluginFailureMode,
    PluginKind,
    PluginManifestV1,
    ProviderNeutralModelRuntime,
    SessionState,
)
from careloop.domain import Turn
from careloop.durable_runtime import (
    DeepSeekModelAdapter,
    OllamaModelAdapter,
    ProviderResponseError,
    VLLMModelAdapter,
)


def _request() -> ModelRequest:
    return ModelRequest(
        contract_version="v1",
        request_id="request-001",
        session_id="session-001",
        input_turn=Turn(
            turn_id="turn-002",
            sequence=1,
            role="user",
            text="Synthetic role-play input.",
        ),
        context_turns=(
            Turn(
                turn_id="turn-001",
                sequence=0,
                role="assistant",
                text="Synthetic context.",
            ),
        ),
        locale="en",
        prompt_template_id="support-shell.v1",
        prompt_template_hash="sha256:" + "a" * 64,
    )


@dataclass
class FakeResponse:
    payload: object
    status_error: BaseException | None = None

    def raise_for_status(self) -> None:
        if self.status_error is not None:
            raise self.status_error

    def json(self) -> object:
        return self.payload


@dataclass
class FakeAsyncClient:
    response: FakeResponse
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"url": url, **kwargs})
        return self.response


def test_deepseek_and_vllm_use_non_streaming_openai_compatible_boundary() -> None:
    for adapter_type, provider_id in (
        (DeepSeekModelAdapter, "deepseek"),
        (VLLMModelAdapter, "vllm-local"),
    ):
        client = FakeAsyncClient(
            FakeResponse({"choices": [{"message": {"content": "Complete draft."}}]})
        )
        adapter = adapter_type(
            provider_id=provider_id,
            model_name="model-001",
            base_url="https://provider.example/v1",
            api_key=SecretStr("server-secret"),
            client=client,
        )

        draft = asyncio.run(adapter.generate(_request()))

        assert draft.provider_id == provider_id
        assert draft.model_name == "model-001"
        assert draft.text == "Complete draft."
        assert draft.draft_id.startswith("draft:sha256:")
        assert client.calls[0]["json"]["stream"] is False
        assert client.calls[0]["json"]["messages"][-1]["role"] == "user"
        assert client.calls[0]["headers"]["Authorization"] == "Bearer server-secret"
        assert "server-secret" not in repr(adapter)


def test_ollama_uses_native_chat_shape_and_keeps_complete_draft_quarantined() -> None:
    client = FakeAsyncClient(
        FakeResponse({"message": {"content": "Ollama complete draft."}})
    )
    adapter = OllamaModelAdapter(
        provider_id="ollama-local",
        model_name="local-model",
        base_url="http://127.0.0.1:11434",
        client=client,
    )

    draft = asyncio.run(adapter.generate(_request()))

    assert draft.text == "Ollama complete draft."
    assert client.calls[0]["url"].endswith("/api/chat")
    assert client.calls[0]["json"]["stream"] is False


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"content": ""}}]},
        {"choices": [{"message": {"content": ["not", "text"]}}]},
    ],
)
def test_malformed_provider_response_fails_visibly_without_fallback(
    payload: object,
) -> None:
    adapter = DeepSeekModelAdapter(
        provider_id="deepseek",
        model_name="model-001",
        base_url="https://provider.example/v1",
        api_key=SecretStr("server-secret"),
        client=FakeAsyncClient(FakeResponse(payload)),
    )

    with pytest.raises(ProviderResponseError):
        asyncio.run(adapter.generate(_request()))


def test_adapter_failure_crosses_existing_runtime_as_category_only_failure() -> None:
    adapter = DeepSeekModelAdapter(
        provider_id="deepseek",
        model_name="model-001",
        base_url="https://provider.example/v1",
        api_key=SecretStr("server-secret"),
        client=FakeAsyncClient(FakeResponse({"choices": []})),
    )
    runtime = ProviderNeutralModelRuntime(
        model_port=adapter,
        provider_manifest=PluginManifestV1(
            plugin_api_version="v1",
            plugin_id="deepseek",
            plugin_version="1.0.0",
            kind=PluginKind.MODEL_PROVIDER,
            capabilities=("synthetic-text-generation",),
            configuration_schema_id="deepseek.config.v1",
            dependency_plugin_ids=(),
            failure_mode=PluginFailureMode.CRITICAL_FAIL_CLOSED,
            default_enabled=False,
        ),
        model_name="model-001",
    )

    result = asyncio.run(
        runtime.generate(
            _request(),
            event_id="event-provider-failure",
            event_sequence=2,
        )
    )

    assert result.failure_code is ModelRuntimeFailureCode.PROVIDER_EXCEPTION
    assert result.event.state_after is SessionState.FAILED_CLOSED
    assert result.quarantined_draft is None
    assert "server-secret" not in result.model_dump_json()
