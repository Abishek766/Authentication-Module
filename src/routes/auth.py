"""Authentication route handlers for registration and login.

Routes are thin: they accept validated Pydantic payloads, delegate all
business logic to AuthService via dependency injection, and return
structured responses. No wiring, no DB access, no business logic here.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.models.schemas import (
    LoginRequest,
    LoginSuccessResponse,
    RegisterRequest,
    RegisterSuccessResponse,
)
from src.services.auth_service import AuthService
from src.services.dependencies import get_auth_service
from src.utils.exceptions import AppError

router = APIRouter(prefix="/api/v1", tags=["Auth"])


@router.post("/register", response_model=RegisterSuccessResponse, status_code=200)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterSuccessResponse:
    """Register a new user account."""
    try:
        return await service.register(payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/login", response_model=LoginSuccessResponse, status_code=200)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginSuccessResponse:
    """Authenticate a user and return JWT access token."""
    try:
        return await service.login(payload)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
