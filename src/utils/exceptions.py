"""Custom exception hierarchy for the user-auth-module.

All domain-level errors raised by the service and repository layers subclass
:class:`AppError`.  Each concrete exception carries a fixed HTTP status
code and a human-readable message sourced from :mod:`src.utils.constants`, so
no caller needs to hard-code either value.

Exception hierarchy::

    AppError (base)
    ├── DuplicateEmailError       → HTTP 409
    ├── DuplicatePhoneError       → HTTP 409
    ├── UserNotFoundError         → HTTP 404
    ├── InvalidCredentialsError   → HTTP 401
    ├── DatabaseError             → HTTP 500
    └── TokenPersistenceError     → HTTP 500

Usage example::

    from src.utils.exceptions import DuplicateEmailError

    raise DuplicateEmailError()
"""

from src.utils.constants import (
    MSG_DUPLICATE_EMAIL,
    MSG_DUPLICATE_PHONE,
    MSG_INTERNAL_ERROR,
    MSG_INVALID_CREDENTIALS,
    MSG_USER_NOT_FOUND,
)


class AppError(Exception):
    """Base application exception.  All domain-level errors subclass this.

    Args:
        message: Human-readable error description forwarded to the API caller.
        status_code: HTTP status code that should be used in the error response.
    """

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DuplicateEmailError(AppError):
    """Raised when a registration attempt uses an already-registered email."""

    def __init__(self) -> None:
        super().__init__(message=MSG_DUPLICATE_EMAIL, status_code=409)


class DuplicatePhoneError(AppError):
    """Raised when a registration attempt uses an already-registered phone number."""

    def __init__(self) -> None:
        super().__init__(message=MSG_DUPLICATE_PHONE, status_code=409)


class UserNotFoundError(AppError):
    """Raised when no user record is found for the given email during login."""

    def __init__(self) -> None:
        super().__init__(message=MSG_USER_NOT_FOUND, status_code=404)


class InvalidCredentialsError(AppError):
    """Raised when password verification fails during login."""

    def __init__(self) -> None:
        super().__init__(message=MSG_INVALID_CREDENTIALS, status_code=401)


class DatabaseError(AppError):
    """Raised when a database operation fails in an unrecoverable way."""

    def __init__(self) -> None:
        super().__init__(message=MSG_INTERNAL_ERROR, status_code=500)


class TokenPersistenceError(AppError):
    """Raised when the refresh token cannot be persisted to the database."""

    def __init__(self) -> None:
        super().__init__(message=MSG_INTERNAL_ERROR, status_code=500)
