from datetime import datetime

from sqlalchemy import DateTime, String, Boolean, text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    hashed_password: Mapped[str | None] = mapped_column( String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column( Boolean, nullable=False, server_default=text("true"))
