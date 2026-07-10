# coding_agent/application/action_parser.py
from __future__ import annotations
import json
import re
from coding_agent.domain.models import Action, ActionType
from coding_agent.infrastructure.llm_provider import LLMResponse


class ActionParser:
    @staticmethod
    def parse(response: LLMResponse) -> Action | None:
        if response.tool_calls:
            tc = response.tool_calls[0]
            return Action(
                type=ActionType.CALL_TOOL,
                tool_name=tc.name,
                tool_args=tc.arguments,
                thought=response.text,
            )

        text = response.text.strip()

        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return ActionParser._from_dict(data)
            except json.JSONDecodeError:
                pass

        try:
            data = json.loads(text)
            return ActionParser._from_dict(data)
        except json.JSONDecodeError:
            pass

        if any(kw in text.lower() for kw in ["done", "task complete", "finished"]):
            return Action(type=ActionType.DONE, thought=text)

        return None

    @staticmethod
    def _from_dict(data: dict) -> Action:
        action_type = ActionType.CALL_TOOL
        type_str = data.get("type", data.get("action", ""))
        if type_str in ("done", "DONE"):
            action_type = ActionType.DONE
        elif type_str in ("take_note", "TAKE_NOTE"):
            action_type = ActionType.TAKE_NOTE

        return Action(
            type=action_type,
            tool_name=data.get("tool_name", data.get("tool")),
            tool_args=data.get("tool_args", data.get("args", {})),
            thought=data.get("thought", ""),
            note=data.get("note"),
        )