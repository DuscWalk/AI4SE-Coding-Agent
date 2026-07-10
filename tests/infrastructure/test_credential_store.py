import pytest
from coding_agent.infrastructure.credential_store import CredentialStore


def test_set_and_get_status():
    store = CredentialStore()
    store.set_api_key("sk-test-key-12345")
    status = store.get_status()
    assert status["configured"] is True
    assert "sk-test" not in str(status)  # no plaintext leak


def test_clear_key():
    store = CredentialStore()
    store.set_api_key("sk-test-key-12345")
    store.clear_api_key()
    status = store.get_status()
    assert status["configured"] is False


def test_status_not_configured():
    store = CredentialStore()
    store.clear_api_key()
    status = store.get_status()
    assert status["configured"] is False