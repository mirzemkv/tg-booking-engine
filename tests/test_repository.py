import asyncio
from datetime import datetime

from sqlalchemy import select

from src.database.models import BookingSlot, Service, User
from src.repositories.booking import BookingRepository


async def create_service_and_slot(
    session_maker,
    start_time: datetime = datetime(2030, 1, 1, 10, 0),
) -> tuple[int, int]:
    async with session_maker() as session:
        service = Service(title="Test Service", price=1000, duration_minutes=60)
        slot = BookingSlot(start_time=start_time, is_booked=False)
        session.add_all([service, slot])
        await session.commit()
        return service.id, slot.id


async def test_get_or_create_user_persists(session_maker):
    async with session_maker() as session:
        repo = BookingRepository(session)
        user = await repo.get_or_create_user(1001, "Test User", "test_user")
        assert user.id == 1001

    async with session_maker() as session:
        assert await session.get(User, 1001) is not None


async def test_get_or_create_user_is_idempotent(session_maker):
    async with session_maker() as session:
        repo = BookingRepository(session)
        first = await repo.get_or_create_user(1002, "Test User")
        second = await repo.get_or_create_user(1002, "Changed Name")
        assert first.id == second.id == 1002

    async with session_maker() as session:
        users = (await session.execute(select(User))).scalars().all()
        assert len(users) == 1


async def test_book_slot_atomic_prevents_double_booking(session_maker):
    service_id, slot_id = await create_service_and_slot(session_maker)

    async with session_maker() as session:
        repo = BookingRepository(session)
        await repo.get_or_create_user(2001, "First User")
        assert await repo.book_slot_atomic(slot_id, 2001, service_id) is True

    async with session_maker() as session:
        repo = BookingRepository(session)
        await repo.get_or_create_user(2002, "Second User")
        assert await repo.book_slot_atomic(slot_id, 2002, service_id) is False


async def test_concurrent_booking_only_one_wins(session_maker):
    service_id, slot_id = await create_service_and_slot(session_maker)

    async def try_book(user_id: int) -> bool:
        async with session_maker() as session:
            repo = BookingRepository(session)
            await repo.get_or_create_user(user_id, f"User {user_id}")
            return await repo.book_slot_atomic(slot_id, user_id, service_id)

    results = await asyncio.gather(try_book(3001), try_book(3002))

    assert sorted(results) == [False, True]


async def test_get_available_slots_excludes_booked(session_maker):
    service_id, booked_slot_id = await create_service_and_slot(
        session_maker,
        start_time=datetime(2030, 1, 1, 10, 0),
    )

    async with session_maker() as session:
        free_slot = BookingSlot(
            start_time=datetime(2030, 1, 1, 11, 0),
            is_booked=False,
        )
        session.add(free_slot)
        await session.commit()
        free_slot_id = free_slot.id

    async with session_maker() as session:
        repo = BookingRepository(session)
        await repo.get_or_create_user(4001, "User")
        assert await repo.book_slot_atomic(booked_slot_id, 4001, service_id) is True

    async with session_maker() as session:
        slots = await BookingRepository(session).get_available_slots()

    assert [slot.id for slot in slots] == [free_slot_id]
