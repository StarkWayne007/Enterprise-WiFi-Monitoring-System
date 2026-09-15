from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    traffic_limit_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1_000_000,
    )

    behavior_window_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1440,
    )

    event_frequency_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )

    technician_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        default="",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

