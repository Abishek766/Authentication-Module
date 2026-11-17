"""Data access layer for user records.

All database read and write operations for the users table live here.
No business logic (hashing, token generation, validation) is performed in
this layer — only raw CRUD operations against the ORM model.
"""

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.schema.user import User


class UserRepository:
    """Provides async CRUD operations for the User ORM model.

    Args:
        session: An active AsyncSession, injected via FastAPI Depends().
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email_or_phone(
        self,
        email: str,
        phone: str,
    ) -> tuple[User | None, User | None]:
        """Check for existing users matching the given email or phone.

        Executes a SINGLE SELECT with an OR predicate so that both checks
        are atomic.  Returns a tuple so callers can distinguish which field
        caused the conflict.

        Args:
            email: The email address to check.
            phone: The phone number to check.

        Returns:
            Tuple (email_match, phone_match) — each is a User or None.
        """
        stmt = select(User).where(
            (func.lower(User.user_email) == email.lower())
            | (User.phone_no == phone)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        email_match: User | None = None
        phone_match: User | None = None
        for row in rows:
            if row.user_email.lower() == email.lower():
                email_match = row
            if row.phone_no == phone:
                phone_match = row

        return email_match, phone_match

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user record by email (case-insensitive).

        Args:
            email: The email address to search for.

        Returns:
            The matching User, or None if not found.
        """
        stmt = select(User).where(func.lower(User.user_email) == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        """Persist a new User record to the database.

        Args:
            user: An unsaved User ORM instance (hashed_password already set).

        Returns:
            The persisted User with the auto-generated id and created_at populated.
        """
        self._session.add(user)
        await self._session.flush()    # assigns id without committing
        await self._session.refresh(user)
        await self._session.commit()
        return user

    async def update_refresh_token(
        self,
        user_id: int,
        refresh_token: str,
    ) -> None:
        """Overwrite the stored refresh token for an existing user.

        Args:
            user_id: The primary key of the user to update.
            refresh_token: The new refresh token string.
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(refresh_token=refresh_token)
        )
        await self._session.execute(stmt)
        await self._session.commit()
