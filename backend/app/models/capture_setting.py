from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CaptureSetting(Base):
    __tablename__ = "capture_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    interface: Mapped[str] = mapped_column(String(50), nullable=False, default="eth0")
    packet_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
