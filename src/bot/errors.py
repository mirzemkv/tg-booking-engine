import logging

from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)


async def handle_error(event: ErrorEvent) -> None:
    logger.error(
        "Unhandled error while processing update",
        exc_info=event.exception,
    )

    update = event.update
    if update.callback_query is not None:
        await update.callback_query.answer(
            "Произошла ошибка. Попробуйте ещё раз: /start",
            show_alert=True,
        )
    elif update.message is not None:
        await update.message.answer(
            "Произошла ошибка. Попробуйте ещё раз: /start"
        )
