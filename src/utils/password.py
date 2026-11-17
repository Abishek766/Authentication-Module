"""Password hashing and verification using bcrypt directly.

Uses the bcrypt library directly instead of passlib, which is unmaintained
and incompatible with bcrypt >= 4.x.
"""

import bcrypt

from src.settings import settings
from src.utils.constants import BCRYPT_WORK_FACTOR


class PasswordHasher:
    """Handles bcrypt password hashing and verification.

    Args:
        rounds: bcrypt work factor (cost). Defaults to BCRYPT_WORK_FACTOR.
    """

    def __init__(self) -> None:
        self._rounds = getattr(settings, "BCRYPT_WORK_FACTOR", BCRYPT_WORK_FACTOR)

    def hash(self, plain: str) -> str:
        """Hash a plaintext password using bcrypt.

        Args:
            plain: The plaintext password string.

        Returns:
            A bcrypt-hashed password string.
        """
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

    def verify(self, plain: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash.

        Args:
            plain: The plaintext password to verify.
            hashed: The bcrypt-hashed password to compare against.

        Returns:
            True if the plaintext matches the hash, False otherwise.
        """
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# Module-level singleton for injection
password_hasher = PasswordHasher()
