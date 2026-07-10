from __future__ import annotations
import json
from pathlib import Path
from coding_agent.domain.models import Session, SessionStatus, StepRecord, AgentResult


class SessionManager:
    def __init__(self, storage_dir: str = "sessions"):
        self._storage = Path(storage_dir)
        self._storage.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, Session] = {}
        self._load_all()

    def create(self, goal: str) -> Session:
        session = Session(goal=goal)
        self._active[session.id] = session
        self._save(session)
        return session

    def get(self, session_id: str) -> Session | None:
        return self._active.get(session_id)

    def add_step(self, session_id: str, step: StepRecord) -> None:
        session = self._active.get(session_id)
        if session:
            session.steps.append(step)
            self._save(session)

    def complete(self, session_id: str, result: AgentResult) -> None:
        session = self._active.get(session_id)
        if session:
            session.result = result
            session.status = SessionStatus.COMPLETED if result.success else SessionStatus.FAILED
            self._save(session)

    def cancel(self, session_id: str) -> None:
        session = self._active.get(session_id)
        if session:
            session.status = SessionStatus.CANCELLED
            self._save(session)

    def list_all(self) -> list[Session]:
        return list(self._active.values())

    def _save(self, session: Session) -> None:
        path = self._storage / f"{session.id}.json"
        path.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    def _load_all(self) -> None:
        for f in self._storage.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                session = Session(**data)
                self._active[session.id] = session
            except Exception:
                pass