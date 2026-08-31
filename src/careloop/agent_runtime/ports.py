"""Dependency-inversion ports for future model adapters."""

from typing import Protocol

from careloop.agent_runtime.contracts import ModelDraft, ModelRequest


class ModelPort(Protocol):
    """Provider-neutral asynchronous model generation boundary."""

    async def generate(self, request: ModelRequest) -> ModelDraft: ...
