"""SQLAlchemy ORM table definition for the users table."""

import datetime

from sqlalchemy import DateTime, Index, String, Text, cast, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    """Represents a registered user in the system.

    Columns:
    - id: Auto-incrementing primary key
    - user_name: Display name (3-50 chars, not unique)
    - user_email: Email address (unique, case-insensitive at DB level)
    - phone_no: 10-digit phone number (unique)
    - hashed_password: bcrypt hash of the user's password
    - refresh_token: Most recent refresh token (nullable, overwritten on each login)
    - created_at: Timestamp of account creation (set by DB server)
    """

    __tablename__ = "User"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(50), nullable=False)
    user_email: Mapped[str] = mapped_column(String(254), nullable=False)
    phone_no: Mapped[str] = mapped_column(String(10), nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        # Case-insensitive unique index on email — cast ensures lower() gets VARCHAR
        Index("uix_users_email", func.lower(cast(user_email, String)), unique=True),
        # Standard unique index on phone number
        Index("uix_users_phone", phone_no, unique=True),
    )
