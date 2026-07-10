from __future__ import annotations
import os
import keyring
import keyring.errors


class CredentialStore:
    SERVICE_NAME = "coding-agent-harness"
    API_KEY_ENTRY = "api_key"

    def set_api_key(self, key: str) -> None:
        try:
            keyring.set_password(self.SERVICE_NAME, self.API_KEY_ENTRY, key)
        except keyring.errors.KeyringError:
            raise RuntimeError(
                "No keyring backend available. Install keyrings.alt on Linux "
                "or configure a desktop keyring service."
            )

    def get_api_key(self) -> str | None:
        try:
            key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
            if key:
                return key
        except keyring.errors.KeyringError:
            pass
        # Fallback to environment variables
        return os.environ.get("CODING_AGENT_API_KEY") or os.environ.get("OPENAI_API_KEY")

    def get_status(self) -> dict:
        try:
            key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
        except keyring.errors.KeyringError:
            key = None
        return {
            "configured": key is not None,
            "masked": "****" if key else None,
        }

    def update_api_key(self, key: str) -> None:
        self.set_api_key(key)

    def clear_api_key(self) -> None:
        try:
            keyring.delete_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
        except keyring.errors.KeyringError:
            pass