from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import (DateTime, ForeignKey, String, func)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column( PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column( ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column( String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column( DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column( DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column( DateTime(timezone=True), server_default=func.now(), nullable=False)
