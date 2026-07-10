from __future__ import annotations
import keyring
import keyring.errors


class CredentialStore:
    SERVICE_NAME = "coding-agent-harness"
    API_KEY_ENTRY = "api_key"

    def set_api_key(self, key: str) -> None:
        keyring.set_password(self.SERVICE_NAME, self.API_KEY_ENTRY, key)

    def get_api_key(self) -> str | None:
        try:
            return keyring.get_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
        except keyring.errors.KeyringError:
            return None

    def get_status(self) -> dict:
        key = self.get_api_key()
        return {
            "configured": key is not None,
            "masked": "****" if key else None,
        }

    def update_api_key(self, key: str) -> None:
        self.set_api_key(key)

    def clear_api_key(self) -> None:
        try:
            keyring.delete_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
        except keyring.errors.PasswordDeleteError:
            pass