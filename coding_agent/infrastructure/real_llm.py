# coding_agent/infrastructure/real_llm.py
"""OpenAI-compatible real LLM provider using the OpenAI SDK."""
from __future__ import annotations
import json
import os
import openai
from coding_agent.infrastructure.llm_provider import LLMProvider, LLMResponse, ToolCall
from coding_agent.domain.models import Message
from coding_agent.infrastructure.credential_store import CredentialStore


class RealLLMProvider(LLMProvider):
    """OpenAI-compatible LLM provider.

    Uses the OpenAI SDK to call any OpenAI-compatible API endpoint.
    Supports function calling (tool use) for agent actions.
    """

    def __init__(
        self,
        credential_store: CredentialStore,
        model_name: str = "gpt-4o",
        base_url: str | None = None,
        timeout: float = 120.0,
    ):
        self._credential_store = credential_store
        self._model_name = model_name
        self._base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self._timeout = timeout

    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        api_key = self._credential_store.get_api_key()
        if not api_key:
            return LLMResponse(
                text="Error: No API key configured. Please set your API key first."
            )

        client_kwargs: dict = {"api_key": api_key, "timeout": self._timeout}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        client = openai.OpenAI(**client_kwargs)

        openai_messages: list[dict] = []
        for m in messages:
            role = m.role
            if role == "system":
                openai_role = "system"
            elif role == "assistant":
                openai_role = "assistant"
            else:
                openai_role = "user"
            openai_messages.append({"role": openai_role, "content": m.content})

        openai_tools: list[dict] = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("parameters", {}),
                },
            })

        kwargs: dict = {
            "model": self._model_name,
            "messages": openai_messages,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        tool_calls: list[ToolCall] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(name=tc.function.name, arguments=args))

        return LLMResponse(
            text=choice.message.content or "",
            tool_calls=tool_calls,
        )