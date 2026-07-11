from __future__ import annotations
import os
from pathlib import Path
import keyring
import keyring.errors
from typing import TypedDict


class CredentialStatus(TypedDict):
    configured: bool
    masked: str | None


class CredentialStore:
    SERVICE_NAME = "coding-agent-harness"
    API_KEY_ENTRY = "api_key"

    def set_api_key(self, key: str) -> None:
        try:
            keyring.set_password(self.SERVICE_NAME, self.API_KEY_ENTRY, key)
        except keyring.errors.KeyringError:
            raise RuntimeError(
                "No secure system keyring is available. Configure Windows "
                "Credential Manager, macOS Keychain, or Linux Secret Service; "
                "for containers, mount a secret file and set "
                "CODING_AGENT_API_KEY_FILE."
            )

    def get_api_key(self) -> str | None:
        try:
            key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_ENTRY)
            if key:
                return key
        except keyring.errors.KeyringError:
            pass
        secret_path = os.environ.get("CODING_AGENT_API_KEY_FILE")
        if secret_path:
            try:
                key = Path(secret_path).read_text(encoding="utf-8").strip()
                if key:
                    return key
            except OSError:
                pass
        # Fallback to environment variables
        return os.environ.get("CODING_AGENT_API_KEY") or os.environ.get("OPENAI_API_KEY")

    def get_status(self) -> CredentialStatus:
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
        except keyring.errors.KeyringError:
            pass
