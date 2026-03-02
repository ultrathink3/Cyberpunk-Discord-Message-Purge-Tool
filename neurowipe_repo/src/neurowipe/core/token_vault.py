"""Encrypted token storage using OS keyring with Fernet fallback."""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from ..constants import FERNET_KEY_FILE, VAULT_SERVICE_NAME
from ..utils.platform_utils import get_config_dir
from .exceptions import VaultError

logger = logging.getLogger("neurowipe.token_vault")


class TokenVault:
    """Stores Discord tokens securely using OS keyring or Fernet encryption."""

    def __init__(self):
        self._use_keyring = True
        try:
            import keyring as _kr
            # Test if keyring backend is available
            _kr.get_password(VAULT_SERVICE_NAME, "__test__")
            self._keyring = _kr
        except Exception:
            logger.warning("Keyring unavailable, falling back to Fernet encryption")
            self._use_keyring = False
            self._keyring = None
        self._fernet = None

    def _get_fernet(self):
        """Get or create Fernet cipher for fallback encryption."""
        if self._fernet:
            return self._fernet

        from cryptography.fernet import Fernet

        key_path = get_config_dir() / FERNET_KEY_FILE
        if key_path.exists():
            key = key_path.read_bytes()
        else:
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            # Restrict permissions
            try:
                os.chmod(key_path, 0o600)
            except OSError:
                pass

        self._fernet = Fernet(key)
        return self._fernet

    def store_token(self, profile_id: str, token: str) -> None:
        """Store a token for a profile."""
        try:
            if self._use_keyring:
                self._keyring.set_password(VAULT_SERVICE_NAME, profile_id, token)
            else:
                fernet = self._get_fernet()
                encrypted = fernet.encrypt(token.encode())
                token_file = get_config_dir() / f"token_{profile_id}.enc"
                token_file.write_bytes(encrypted)
                try:
                    os.chmod(token_file, 0o600)
                except OSError:
                    pass
            logger.debug(f"Token stored for profile {profile_id}")
        except Exception as e:
            raise VaultError(f"Failed to store token: {e}") from e

    def get_token(self, profile_id: str) -> str | None:
        """Retrieve a token for a profile."""
        try:
            if self._use_keyring:
                return self._keyring.get_password(VAULT_SERVICE_NAME, profile_id)
            else:
                fernet = self._get_fernet()
                token_file = get_config_dir() / f"token_{profile_id}.enc"
                if not token_file.exists():
                    return None
                encrypted = token_file.read_bytes()
                return fernet.decrypt(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to retrieve token for profile {profile_id}: {e}")
            return None

    def delete_token(self, profile_id: str) -> None:
        """Delete a token for a profile."""
        try:
            if self._use_keyring:
                try:
                    self._keyring.delete_password(VAULT_SERVICE_NAME, profile_id)
                except Exception:
                    pass  # May not exist
            else:
                token_file = get_config_dir() / f"token_{profile_id}.enc"
                if token_file.exists():
                    token_file.unlink()
            logger.debug(f"Token deleted for profile {profile_id}")
        except Exception as e:
            logger.warning(f"Failed to delete token for profile {profile_id}: {e}")

    def has_token(self, profile_id: str) -> bool:
        """Check if a token exists for a profile."""
        return self.get_token(profile_id) is not None
