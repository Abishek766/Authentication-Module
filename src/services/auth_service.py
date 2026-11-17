"""Authentication business logic for registration and login.

Implements the AuthService class which orchestrates the full register and login
flows, delegating persistence to UserRepository and cryptographic operations to
PasswordHasher and JWTHandler.

This layer is framework-agnostic: no FastAPI imports, no Pydantic validation.
All validation is assumed to have been performed by the Pydantic models at the
route layer before reaching this service.

Responsibility:
- Enforce uniqueness constraints (email, phone) before writing to the DB.
- Never expose raw database or driver error text to callers.
- Translate repository/utility exceptions into typed AppError subclasses.
- Log every caught exception at ERROR level with full stack trace.
"""

from sqlalchemy.exc import SQLAlchemyError

from src.models.schema.user import User
from src.models.schemas import (
    LoginRequest,
    LoginSuccessResponse,
    RegisterRequest,
    RegisterSuccessResponse,
)
from src.repositories.user_repository import UserRepository
from src.utils.exceptions import (
    DatabaseError,
    DuplicateEmailError,
    DuplicatePhoneError,
    InvalidCredentialsError,
    TokenPersistenceError,
    UserNotFoundError,
)
from src.utils.jwt_handler import JWTHandler
from src.utils.logger import logger
from src.utils.password import PasswordHasher


class AuthService:
    """Orchestrates authentication business logic.

    Depends on three injected collaborators so the service stays testable
    and framework-agnostic:

    Args:
        repo: Data-access object for user persistence queries.
        hasher: bcrypt password hashing and verification utility.
        jwt_handler: JWT access and refresh token creation utility.
    """

    def __init__(
        self,
        repo: UserRepository,
        hasher: PasswordHasher,
        jwt_handler: JWTHandler,
    ) -> None:
        self._repo = repo
        self._hasher = hasher
        self._jwt = jwt_handler

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, payload: RegisterRequest) -> RegisterSuccessResponse:
        """Register a new user account.

        Flow:
        1. Check for existing email / phone conflicts.
        2. Hash the supplied plaintext password.
        3. Persist the new User record to the database.
        4. Return a success response.

        Args:
            payload: Validated registration data (name, email, phone, password).

        Returns:
            RegisterSuccessResponse with HTTP 200 status and success message.

        Raises:
            DuplicateEmailError: Email is already registered (HTTP 409).
            DuplicatePhoneError: Phone number is already registered (HTTP 409).
            DatabaseError: Any database or hashing failure (HTTP 500).
        """
        # Step 1 — duplicate check (single query, two results)
        email_match, phone_match = await self._repo.get_by_email_or_phone(
            payload.user_email, payload.phone_no
        )

        # Step 2 — email conflict
        if email_match is not None:
            raise DuplicateEmailError()

        # Step 3 — phone conflict
        if phone_match is not None:
            raise DuplicatePhoneError()

        # Step 4 — hash password; wrap any hashing failure as DatabaseError
        try:
            hashed = self._hasher.hash(payload.password)
        except Exception as exc:
            logger.exception("Password hashing failed during registration: %s", exc)
            raise DatabaseError() from exc

        # Step 5 — build ORM instance (no auto-flush; session managed by repo)
        user = User(
            user_name=payload.user_name,
            user_email=payload.user_email,
            phone_no=payload.phone_no,
            hashed_password=hashed,
        )

        # Step 6 — persist; wrap SQLAlchemy errors
        try:
            await self._repo.create_user(user)
        except SQLAlchemyError as exc:
            logger.exception("Database error while creating user: %s", exc)
            raise DatabaseError() from exc

        # Step 7 — success
        return RegisterSuccessResponse()

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(self, payload: LoginRequest) -> LoginSuccessResponse:
        """Authenticate a user and issue JWT tokens.

        Flow:
        1. Look up user by email.
        2. Verify the submitted password against the stored hash.
        3. Generate access and refresh tokens.
        4. Persist the refresh token for future rotation/revocation.
        5. Return a success response containing the access token.

        Args:
            payload: Validated login data (email, password).

        Returns:
            LoginSuccessResponse containing the JWT access token.

        Raises:
            UserNotFoundError: No account found for the given email (HTTP 404).
            InvalidCredentialsError: Password verification failed (HTTP 401).
            DatabaseError: Error fetching the user record (HTTP 500).
            TokenPersistenceError: Error persisting the refresh token (HTTP 500).
        """
        # Step 1 — look up user by email; wrap DB errors
        try:
            user = await self._repo.get_by_email(payload.user_email)
        except SQLAlchemyError as exc:
            logger.exception("Database error while fetching user by email: %s", exc)
            raise DatabaseError() from exc

        # Step 2 — user must exist
        if user is None:
            raise UserNotFoundError()

        # Step 3 — password verification; wrong password → 401
        if not self._hasher.verify(payload.password, user.hashed_password):
            raise InvalidCredentialsError()

        # Step 4 — build JWT payloads
        token_payload = {"sub": str(user.id), "email": user.user_email}

        # Step 5 — create access token
        access_token = self._jwt.create_access_token(token_payload)

        # Step 6 — create refresh token (only sub claim; email not needed here)
        refresh_token = self._jwt.create_refresh_token({"sub": str(user.id)})

        # Step 7 — persist refresh token; wrap DB errors
        try:
            await self._repo.update_refresh_token(user.id, refresh_token)
        except SQLAlchemyError as exc:
            logger.exception("Database error while persisting refresh token: %s", exc)
            raise TokenPersistenceError() from exc

        # Step 8 — success
        return LoginSuccessResponse(access_token=access_token)
