# coding_agent/infrastructure/llm_provider.py
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from coding_agent.domain.models import Message


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        ...


class ScriptedMockLLM(LLMProvider):
    def __init__(self, responses: list[LLMResponse]):
        self._responses = responses
        self._index = 0

    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        if self._index >= len(self._responses):
            raise IndexError("No more scripted responses")
        response = self._responses[self._index]
        self._index += 1
        return response


class RuleBasedMockLLM(LLMProvider):
    def __init__(self, rules: list[tuple[callable, LLMResponse]]):
        self._rules = rules

    def chat(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        for condition, response in self._rules:
            if condition(messages, tools):
                return response
        return LLMResponse(text="no matching rule", tool_calls=[])