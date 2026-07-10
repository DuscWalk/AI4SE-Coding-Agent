# coding_agent/domain/memory.py
from __future__ import annotations
import datetime
import hashlib
from coding_agent.domain.models import Message, MemoryEntry, MemoryType
from coding_agent.infrastructure.vector_store import VectorStore


class MemoryManager:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.session_notes: list[MemoryEntry] = []

    def read(self, goal: str) -> list[MemoryEntry]:
        embedding = self._simple_embed(goal)
        entries = self.vector_store.search(goal, embedding, top_k=5)
        # Also include matching scratchpad notes
        for note in self.session_notes:
            if goal.lower() in note.content.lower():
                entries.append(note)
        return entries  # type: ignore[return-value]

    def write(self, note: str) -> None:
        entry = MemoryEntry(
            content=note,
            timestamp=datetime.datetime.now(),
            type=MemoryType.SCRATCHPAD,
        )
        self.session_notes.append(entry)

    def consolidate(self) -> None:
        for note in self.session_notes:
            embedding = self._simple_embed(note.content)
            self.vector_store.insert(note.content, embedding)
        self.session_notes = []

    def compress(self, context: list[Message], max_recent: int = 6) -> list[Message]:
        if len(context) <= max_recent:
            return context
        system = [m for m in context if m.role == "system"]
        recent = context[-max_recent:]
        summary = "Earlier conversation summary:\n"
        for m in context[len(system):-max_recent]:
            summary += f"[{m.role}]: {m.content[:200]}\n"
        return system + [Message(role="user", content=summary)] + recent

    def _simple_embed(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h[:32]]