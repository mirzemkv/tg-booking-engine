from collections.abc import Sequence
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import BookingSlot, Service, User


class BookingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(
        self, user_id: int, full_name: str, username: str | None = None
    ) -> User:
        user = await self.session.get(User, user_id)
        if user:
            return user

        user = User(id=user_id, full_name=full_name, username=username)
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError:
            # Concurrent /start from the same user: another request inserted the row.
            await self.session.rollback()
            user = await self.session.get(User, user_id)
            if user is None:
                raise
        return user

    async def get_services(self) -> Sequence[Service]:
        result = await self.session.execute(select(Service))
        return result.scalars().all()

    async def get_available_slots(self) -> Sequence[BookingSlot]:
        stmt = (
            select(BookingSlot)
            .where(BookingSlot.is_booked.is_(False))
            .order_by(BookingSlot.start_time)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def book_slot_atomic(
        self, slot_id: int, user_id: int, service_id: int
    ) -> bool:
        stmt = (
            select(BookingSlot)
            .where(BookingSlot.id == slot_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        slot = result.scalar_one_or_none()

        if not slot or slot.is_booked:
            await self.session.rollback()
            return False

        slot.is_booked = True
        slot.user_id = user_id
        slot.service_id = service_id
        await self.session.commit()
        return True
