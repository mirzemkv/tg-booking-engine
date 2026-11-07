import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from src.database.models import BookingSlot, Service
from src.database.session import async_session_maker, engine

DEFAULT_SERVICES = (
    {"title": "Консультация", "price": 3000, "duration_minutes": 60},
    {"title": "Массаж", "price": 4500, "duration_minutes": 90},
    {"title": "Онлайн-встреча", "price": 2000, "duration_minutes": 45},
)

SLOT_HOURS = (10, 12, 14, 16, 18)
SEED_DAYS = 7


async def seed() -> None:
    async with async_session_maker() as session:
        services = (await session.execute(select(Service))).scalars().all()
        if services:
            print(f"Services: already present ({len(services)}), skipping.")
        else:
            session.add_all([Service(**data) for data in DEFAULT_SERVICES])
            await session.commit()
            print(f"Services: created {len(DEFAULT_SERVICES)} demo services.")

        now = datetime.now()
        existing_slot = (
            await session.execute(
                select(BookingSlot)
                .where(BookingSlot.start_time >= now)
                .limit(1)
            )
        ).scalar_one_or_none()

        if existing_slot is not None:
            print("Slots: future slots already exist, skipping.")
        else:
            slots: list[BookingSlot] = []
            for day in range(1, SEED_DAYS + 1):
                day_start = (now + timedelta(days=day)).replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
                slots.extend(
                    BookingSlot(start_time=day_start.replace(hour=hour))
                    for hour in SLOT_HOURS
                )

            session.add_all(slots)
            await session.commit()
            print(
                f"Slots: created {len(slots)} slots "
                f"for the next {SEED_DAYS} days."
            )

    print("Seeding complete.")


async def main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
