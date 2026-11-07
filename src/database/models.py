from datetime import UTC, datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.base import Base


def utc_now() -> datetime:
    """Return a timezone-naive UTC timestamp for DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(128))
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    bookings: Mapped[list["BookingSlot"]] = relationship(back_populates="user")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)

    slots: Mapped[list["BookingSlot"]] = relationship(back_populates="service")


class BookingSlot(Base):
    __tablename__ = "booking_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    service: Mapped[Service | None] = relationship(back_populates="slots")
    user: Mapped[User | None] = relationship(back_populates="bookings")
