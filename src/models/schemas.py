"""Pydantic v2 request and response schemas for the auth API.

Implements all input validation per the API contract defined in openapi.yaml.
Password strength validation accumulates all failures before raising so that
callers receive a single, complete error response.

"""

import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.utils.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    PHONE_PATTERN,
    USER_NAME_MAX_LENGTH,
    USER_NAME_MIN_LENGTH,
)


class RegisterRequest(BaseModel):
    user_name: Annotated[
        str,
        Field(min_length=USER_NAME_MIN_LENGTH, max_length=USER_NAME_MAX_LENGTH),
    ]
    user_email: EmailStr
    phone_no: Annotated[str, Field(pattern=PHONE_PATTERN)]
    password: Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH)]

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate that the password meets all character-class requirements.

        All failing checks are accumulated and reported in a single ValueError
        so that the caller receives one complete error message rather than
        having to submit the form multiple times to discover each rule.
        """
        errors: list[str] = []

        if not re.search(r"[A-Z]", v):
            errors.append("at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("at least one lowercase letter")
        if not re.search(r"\d", v):
            errors.append("at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("at least one special character")

        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")

        return v


class RegisterSuccessResponse(BaseModel):
    status_code: int = 200
    message: str = "User profile created successfully"


class LoginRequest(BaseModel):
    user_email: Annotated[EmailStr, Field(max_length=EMAIL_MAX_LENGTH)]
    password: Annotated[str, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]


class LoginSuccessResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    message: str = "Login successfully"


class ErrorResponse(BaseModel):
    status_code: int
    message: str
