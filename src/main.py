import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from src.bot.errors import handle_error
from src.bot.handlers.booking import router as booking_router
from src.core.config import settings
from src.database.session import engine


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    redis_client = Redis.from_url(settings.redis_url)
    storage = RedisStorage(redis=redis_client)

    bot = Bot(token=settings.BOT_TOKEN.get_secret_value())
    dp = Dispatcher(storage=storage)
    dp.errors.register(handle_error)
    dp.include_router(booking_router)

    logging.info("Starting bot long-polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await redis_client.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
