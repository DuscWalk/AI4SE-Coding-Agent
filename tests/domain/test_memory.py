# tests/domain/test_memory.py
from coding_agent.domain.memory import MemoryManager
from coding_agent.infrastructure.vector_store import InMemoryVectorStore


def test_write_and_read_scratchpad():
    mm = MemoryManager(InMemoryVectorStore())
    mm.write("use pytest for testing")
    memories = mm.read("testing")
    assert len(memories) > 0


def test_consolidate():
    mm = MemoryManager(InMemoryVectorStore())
    mm.write("important decision: use FastAPI")
    mm.consolidate()
    memories = mm.read("FastAPI")
    assert any("FastAPI" in m.content for m in memories)


def test_compress_context():
    mm = MemoryManager(InMemoryVectorStore())
    from coding_agent.domain.models import Message
    context = [Message(role="system", content="you are a coding agent")]
    for i in range(20):
        context.append(Message(role="user", content=f"message {i}"))
        context.append(Message(role="assistant", content=f"response {i}"))
    compressed = mm.compress(context, max_recent=4)
    assert len(compressed) < len(context)