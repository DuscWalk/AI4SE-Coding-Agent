# tests/infrastructure/test_vector_store.py
from coding_agent.infrastructure.vector_store import InMemoryVectorStore


def test_insert_and_search():
    store = InMemoryVectorStore()
    store.insert("project uses pytest", [0.1, 0.2, 0.3])
    store.insert("code style is PEP 8", [0.1, 0.2, 0.4])
    results = store.search("testing", [0.1, 0.2, 0.3])
    assert len(results) == 2
    assert "pytest" in results[0].content


def test_search_empty_store():
    store = InMemoryVectorStore()
    results = store.search("query", [0.0, 0.0, 0.0])
    assert len(results) == 0


def test_delete_entry():
    store = InMemoryVectorStore()
    store.insert("test memory", [0.5, 0.5])
    store.delete("test memory")
    results = store.search("memory", [0.5, 0.5])
    assert len(results) == 0