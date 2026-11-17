"""JWT access and refresh token creation and decoding.

Uses python-jose for HS256 JWT operations. Signing secret and token
expiry values are read from application settings.
"""

from datetime import UTC, datetime, timedelta

from jose import jwt

from src.settings import settings
from src.utils.constants import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

ALGORITHM = "HS256"


class JWTHandler:
    """Creates and decodes HS256 JWT access and refresh tokens.

    Token lifetime:
    - Access token: ≤ 30 minutes (ACCESS_TOKEN_EXPIRE_MINUTES)
    - Refresh token: ≥ 7 days (REFRESH_TOKEN_EXPIRE_DAYS)

    Each token includes an `iat` (issued-at) claim to guarantee uniqueness
    across sequential logins for the same user.
    """

    def create_access_token(self, payload: dict) -> str:
        """Create a signed JWT access token.

        Args:
            payload: Claims to embed. Must not include `exp` or `iat`.

        Returns:
            Signed JWT string.
        """
        now = datetime.now(tz=UTC)
        expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", ACCESS_TOKEN_EXPIRE_MINUTES)
        data = {
            **payload,
            "iat": now,
            "exp": now + timedelta(minutes=expire_minutes),
        }
        return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)

    def create_refresh_token(self, payload: dict) -> str:
        """Create a signed JWT refresh token with longer expiry.

        Args:
            payload: Claims to embed. Must not include `exp` or `iat`.

        Returns:
            Signed JWT string.
        """
        now = datetime.now(tz=UTC)
        expire_days = getattr(settings, "REFRESH_TOKEN_EXPIRE_DAYS", REFRESH_TOKEN_EXPIRE_DAYS)
        data = {
            **payload,
            "iat": now,
            "exp": now + timedelta(days=expire_days),
        }
        return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)

    def decode_token(self, token: str) -> dict:
        """Decode and verify a JWT token.

        Args:
            token: The encoded JWT string.

        Returns:
            Decoded payload dict.

        Raises:
            JWTError: If the token is invalid, expired, or tampered.
        """
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])


# Module-level singleton for injection
jwt_handler = JWTHandler()
