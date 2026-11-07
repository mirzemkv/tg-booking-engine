from collections.abc import Sequence
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from src.database.models import BookingSlot, Service


def get_services_kb(services: Sequence[Service]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{s.title} — {s.price} ₽",
                callback_data=f"srv_{s.id}",
            )
        ]
        for s in services
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_slots_kb(slots: Sequence[BookingSlot]) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=slot.start_time.strftime("%d.%m %H:%M"),
                callback_data=f"slot_{slot.id}",
            )
        ]
        for slot in slots
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
