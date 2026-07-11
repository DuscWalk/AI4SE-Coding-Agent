import keyring.errors
import pytest

from coding_agent.infrastructure.credential_store import CredentialStore


@pytest.fixture
def fake_keyring(monkeypatch):
    values: dict[tuple[str, str], str] = {}

    def set_password(service: str, entry: str, value: str) -> None:
        values[(service, entry)] = value

    def get_password(service: str, entry: str) -> str | None:
        return values.get((service, entry))

    def delete_password(service: str, entry: str) -> None:
        values.pop((service, entry), None)

    monkeypatch.setattr(
        "coding_agent.infrastructure.credential_store.keyring.set_password",
        set_password,
    )
    monkeypatch.setattr(
        "coding_agent.infrastructure.credential_store.keyring.get_password",
        get_password,
    )
    monkeypatch.setattr(
        "coding_agent.infrastructure.credential_store.keyring.delete_password",
        delete_password,
    )
    return values


def test_set_and_get_status(fake_keyring) -> None:
    store = CredentialStore()
    store.set_api_key("sk-test-key-12345")
    status = store.get_status()
    assert status["configured"] is True
    assert "sk-test" not in str(status)  # no plaintext leak


def test_clear_key(monkeypatch, fake_keyring) -> None:
    monkeypatch.delenv("CODING_AGENT_API_KEY_FILE", raising=False)
    monkeypatch.delenv("CODING_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = CredentialStore()
    store.set_api_key("sk-test-key-12345")
    store.clear_api_key()
    status = store.get_status()
    assert status["configured"] is False


def test_status_not_configured(monkeypatch, fake_keyring) -> None:
    monkeypatch.delenv("CODING_AGENT_API_KEY_FILE", raising=False)
    monkeypatch.delenv("CODING_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    store = CredentialStore()
    store.clear_api_key()
    status = store.get_status()
    assert status["configured"] is False


def test_get_api_key_from_secret_file(
    tmp_path, monkeypatch,
) -> None:
    secret_file = tmp_path / "api-key"
    secret_file.write_text("sk-secret-file-key\n", encoding="utf-8")
    monkeypatch.setenv("CODING_AGENT_API_KEY_FILE", str(secret_file))
    monkeypatch.delenv("CODING_AGENT_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        "coding_agent.infrastructure.credential_store.keyring.get_password",
        lambda *_args: None,
    )

    store = CredentialStore()

    assert store.get_api_key() == "sk-secret-file-key"
    assert store.get_status() == {"configured": True, "masked": "****"}


def test_set_api_key_rejects_missing_secure_keyring(monkeypatch) -> None:
    def raise_no_keyring(*_args) -> None:
        raise keyring.errors.NoKeyringError()

    monkeypatch.setattr(
        "coding_agent.infrastructure.credential_store.keyring.set_password",
        raise_no_keyring,
    )

    with pytest.raises(RuntimeError, match="system keyring"):
        CredentialStore().set_api_key("sk-test-key")
