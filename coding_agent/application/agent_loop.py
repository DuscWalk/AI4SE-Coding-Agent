# coding_agent/application/agent_loop.py
"""AgentLoop: main loop orchestrating all harness components."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable

from coding_agent.domain.models import Action, ActionType, AgentResult, Message, StepRecord
from coding_agent.domain.tool_manager import ToolManager
from coding_agent.domain.governance import Governance, Permission
from coding_agent.domain.feedback.pipeline import FeedbackPipeline
from coding_agent.application.action_parser import ActionParser
from coding_agent.application.session_manager import SessionManager
from coding_agent.domain.memory import MemoryManager
from coding_agent.domain.config import Config
from coding_agent.infrastructure.llm_provider import LLMProvider


class AgentLoop:
    """Main agent loop that orchestrates LLM, tools, governance, feedback, memory.

    Lifecycle per invocation:
      1. Build initial context from goal, project rules, and memory.
      2. Loop: call LLM -> parse action -> governance check -> dispatch tool
         -> run feedback pipeline -> compress context.
      3. Stop on DONE action, max steps exceeded, or unrecoverable error.

    HITL support: when governance returns NEEDS_HITL or NEEDS_CONFIRMATION,
    the loop blocks on a threading.Event until the WebUI approve/deny endpoint
    signals it. Timeout is 5 minutes (configurable via HITLState).
    """

    LLM_MAX_RETRIES = 3
    LLM_TIMEOUT = 120.0  # seconds

    def __init__(
        self,
        llm: LLMProvider,
        tool_manager: ToolManager,
        governance: Governance,
        feedback_pipeline: FeedbackPipeline,
        action_parser: ActionParser,
        session_manager: SessionManager,
        memory: MemoryManager,
        config: Config,
        hitl_enabled: bool = False,
    ):
        self.llm = llm
        self.tool_manager = tool_manager
        self.governance = governance
        self.feedback_pipeline = feedback_pipeline
        self.action_parser = action_parser
        self.session_manager = session_manager
        self.memory = memory
        self.config = config
        self.hitl_enabled = hitl_enabled
        self._hitl_events: dict[str, threading.Event] = {}
        self._hitl_approved: dict[str, bool] = {}
        self._step_callbacks: list[Callable] = []

    def on_step(self, callback: Callable) -> None:
        """Register a callback invoked after each step.

        The callback receives (session_id, step_number, action, result, status).
        Called from the agent loop thread — callbacks must be thread-safe.
        """
        self._step_callbacks.append(callback)

    def approve_session(self, session_id: str) -> None:
        """Signal HITL approval for a waiting session."""
        event = self._hitl_events.get(session_id)
        if event is not None:
            self._hitl_approved[session_id] = True
            event.set()

    def deny_session(self, session_id: str) -> None:
        """Signal HITL denial for a waiting session."""
        event = self._hitl_events.get(session_id)
        if event is not None:
            self._hitl_approved[session_id] = False
            event.set()

    def _await_hitl(self, session_id: str, timeout_s: int = 300) -> bool:
        """Block until HITL is resolved or timeout.

        Returns True if approved, False if denied or timed out.
        """
        event = threading.Event()
        self._hitl_events[session_id] = event
        self._hitl_approved[session_id] = False
        try:
            resolved = event.wait(timeout=timeout_s)
            if not resolved:
                return False  # timeout = denied
            return self._hitl_approved.get(session_id, False)
        finally:
            self._hitl_events.pop(session_id, None)
            self._hitl_approved.pop(session_id, None)

    def _notify_step(self, session_id: str, step_number: int,
                     action: Action | None, result, status: str) -> None:
        """Notify all registered step callbacks."""
        for cb in self._step_callbacks:
            try:
                cb(session_id, step_number, action, result, status)
            except Exception:
                pass

    def _call_llm(self, context: list[Message]) -> LLMProvider.LLMResponse | None:
        """Call LLM with retry and timeout.

        Retries up to LLM_MAX_RETRIES on failure.
        Returns None if all retries are exhausted.
        """
        import concurrent.futures

        for attempt in range(1, self.LLM_MAX_RETRIES + 1):
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        self.llm.chat, context, self.tool_manager.list_defs()
                    )
                    return future.result(timeout=self.LLM_TIMEOUT)
            except concurrent.futures.TimeoutError:
                if attempt < self.LLM_MAX_RETRIES:
                    continue
            except Exception:
                if attempt < self.LLM_MAX_RETRIES:
                    time.sleep(0.5)
                    continue

        return None

    def run(self, goal: str) -> AgentResult:
        """Execute the agent loop for a given goal.

        Args:
            goal: The user's task description.

        Returns:
            AgentResult with success flag, answer text, and optional error.
        """
        session = self.session_manager.create(goal)
        session_id = session.id
        context = self._build_context(goal)
        steps = 0

        while steps < self.config.max_steps:
            steps += 1

            # Compress context if approaching token limit
            if self._context_too_large(context):
                context = self.memory.compress(context)

            # 1. Call LLM (with retry and timeout)
            response = self._call_llm(context)
            if response is None:
                result = AgentResult(
                    success=False,
                    error="LLM call failed after retries or timed out",
                )
                self.session_manager.complete(session_id, result)
                self._notify_step(session_id, steps, None, result, "failed")
                return result

            # 2. Parse action from LLM response
            action = self.action_parser.parse(response)

            # Always record assistant response in context
            context.append(Message(role="assistant", content=response.text))

            # Handle unparseable response
            if action is None:
                context.append(Message(
                    role="user",
                    content="Invalid action format. Please use CALL_TOOL, DONE, or TAKE_NOTE.",
                ))
                continue

            # 3. Handle DONE action
            if action.type == ActionType.DONE:
                result = AgentResult(success=True, answer=response.text)
                self.session_manager.complete(session_id, result)
                self._notify_step(session_id, steps, action, result, "done")
                return result

            # 4. Handle TAKE_NOTE action
            if action.type == ActionType.TAKE_NOTE:
                self.memory.write(action.note or "")
                continue

            # 5. Governance check
            permission_result = self.governance.check(action)

            if permission_result.permission == Permission.BLOCKED:
                context.append(Message(
                    role="user",
                    content="Action blocked by governance guardrail.",
                ))
                step = StepRecord(step_number=steps, action=action,
                                  governance_result={"permission": "BLOCKED", "reason": permission_result.reason})
                self.session_manager.add_step(session_id, step)
                self._notify_step(session_id, steps, action, None, "blocked")
                continue

            if permission_result.permission in (Permission.NEEDS_CONFIRMATION, Permission.NEEDS_HITL):
                if not self.hitl_enabled:
                    # HITL disabled — treat as blocked
                    context.append(Message(
                        role="user",
                        content=f"Action requires approval ({permission_result.permission.value}) but HITL is disabled.",
                    ))
                    step = StepRecord(step_number=steps, action=action,
                                      governance_result={"permission": permission_result.permission.value, "reason": "HITL disabled"})
                    self.session_manager.add_step(session_id, step)
                    self._notify_step(session_id, steps, action, None, "blocked")
                    continue
                # Notify frontend that HITL is needed
                self._notify_step(session_id, steps, action, None, "awaiting_approval")
                # Block until approved, denied, or timed out
                approved = self._await_hitl(session_id)
                if not approved:
                    context.append(Message(
                        role="user",
                        content="Action was denied or timed out.",
                    ))
                    step = StepRecord(step_number=steps, action=action,
                                      governance_result={"permission": permission_result.permission.value, "reason": "denied or timed out"})
                    self.session_manager.add_step(session_id, step)
                    self._notify_step(session_id, steps, action, None, "denied")
                    continue
                # Approved — fall through to dispatch

            # 6. Dispatch tool
            result = self.tool_manager.dispatch(action)
            context.append(Message(role="user", content=result.output))
            step = StepRecord(step_number=steps, action=action, action_result=result)
            self.session_manager.add_step(session_id, step)

            # 7. Run feedback pipeline on changed files
            if result.changed_files:
                fb_result = self.feedback_pipeline.run(result.changed_files)
                if fb_result.feedback_text:
                    context.append(Message(role="user", content=fb_result.feedback_text))

            self._notify_step(session_id, steps, action, result, "completed")

        # Max steps exceeded
        result = AgentResult(success=False, error="Max steps reached")
        self.session_manager.complete(session_id, result)
        self._notify_step(session_id, steps, None, result, "max_steps")
        return result

    def _build_context(self, goal: str) -> list[Message]:
        """Build the initial message context for the LLM."""
        context: list[Message] = [
            Message(
                role="system",
                content=(
                    "You are a coding agent. You can read/write files, "
                    "run shell commands, and execute tests. "
                    "Respond with tool calls to take action, or just text when done."
                ),
            ),
        ]

        if self.config.project_rules:
            context.append(Message(
                role="user",
                content=f"Project rules:\n{self.config.project_rules}",
            ))

        memories = self.memory.read(goal)
        for m in memories:
            context.append(Message(
                role="user",
                content=f"Memory: {m.content}",
            ))

        context.append(Message(role="user", content=goal))
        return context

    def _context_too_large(self, context: list[Message]) -> bool:
        """Check if the context is approaching the token limit.

        Uses a rough heuristic: 1 token ≈ 4 characters.
        """
        total = sum(len(m.content) for m in context)
        return total > self.config.max_context_tokens * 4