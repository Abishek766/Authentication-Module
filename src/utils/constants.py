"""Application-wide constants for the user-auth-module.

All magic numbers and fixed string literals are centralised here so that
no other module hard-codes values directly.  Import individual names as
needed:

    from src.utils.constants import BCRYPT_WORK_FACTOR, MSG_LOGIN_SUCCESS

Constants are grouped into two logical sections:
  - Validation constraints  — numeric and pattern limits used by Pydantic models
                              and security utilities.
  - Response messages       — human-readable strings returned in API response bodies.
"""

# ---------------------------------------------------------------------------
# Validation constraints
# ---------------------------------------------------------------------------

BCRYPT_WORK_FACTOR: int = 12
"""Number of bcrypt hashing rounds.  Must be ≥ 12 for production security."""

ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
"""Lifetime of a JWT access token in minutes (≤ 30 per security policy)."""

REFRESH_TOKEN_EXPIRE_DAYS: int = 7
"""Lifetime of a JWT refresh token in days (≥ 7 per security policy)."""

PASSWORD_MIN_LENGTH: int = 8
"""Minimum number of characters required in a user password."""

PASSWORD_MAX_LENGTH: int = 128
"""Maximum number of characters allowed in a user password."""

USER_NAME_MIN_LENGTH: int = 3
"""Minimum number of characters required in a username."""

USER_NAME_MAX_LENGTH: int = 50
"""Maximum number of characters allowed in a username."""

PHONE_PATTERN: str = r"^[0-9]{10}$"
"""Regex pattern that a valid phone number must match: exactly 10 digits."""

EMAIL_MAX_LENGTH: int = 254
"""Maximum email address length per RFC 5321 / RFC 5322."""

DB_READY_TIMEOUT_SECONDS: int = 5
"""Seconds to wait for a database probe in the /ready endpoint before timing out."""

# ---------------------------------------------------------------------------
# Response messages
# ---------------------------------------------------------------------------

MSG_REGISTRATION_SUCCESS: str = "User profile created successfully"
"""Returned in the response body after a successful user registration."""

MSG_LOGIN_SUCCESS: str = "Login successfully"
"""Returned in the response body after a successful login."""

MSG_INTERNAL_ERROR: str = "Something went wrong. Please try again later"
"""Generic error message for unexpected server-side failures (HTTP 500)."""

MSG_USER_NOT_FOUND: str = "User not found"
"""Returned when a login attempt references an unregistered email (HTTP 404)."""

MSG_INVALID_CREDENTIALS: str = "Invalid email or password"
"""Returned when a login attempt fails password verification (HTTP 401)."""

MSG_DUPLICATE_EMAIL: str = "User already exists with this email"
"""Returned when registration is attempted with an already-registered email (HTTP 409)."""

MSG_DUPLICATE_PHONE: str = "User already exists with this phone number"
"""Returned when registration is attempted with an already-registered phone number (HTTP 409)."""
