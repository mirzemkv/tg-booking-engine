from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from src.bot.keyboards.inline import get_services_kb, get_slots_kb
from src.bot.states.booking import BookingFSM
from src.database.session import async_session_maker
from src.repositories.booking import BookingRepository

router = Router(name="booking_router")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        repo = BookingRepository(session)
        await repo.get_or_create_user(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )
        await session.commit()
        services = await repo.get_services()

    if not services:
        await message.answer("В данный момент нет доступных услуг.")
        return

    await state.set_state(BookingFSM.choosing_service)
    await message.answer(
        "Добро пожаловать! Выберите услугу для записи:",
        reply_markup=get_services_kb(services),
    )


@router.callback_query(BookingFSM.choosing_service, F.data.startswith("srv_"))
async def service_selected(callback: CallbackQuery, state: FSMContext):
    service_id = int(callback.data.split("_")[1])
    await state.update_data(service_id=service_id)

    async with async_session_maker() as session:
        repo = BookingRepository(session)
        slots = await repo.get_available_slots()

    if not slots:
        await callback.message.edit_text("К сожалению, свободных окон нет.")
        await state.clear()
        return

    await state.set_state(BookingFSM.choosing_slot)
    await callback.message.edit_text(
        "Выберите удобное время:",
        reply_markup=get_slots_kb(slots),
    )
    await callback.answer()


@router.callback_query(BookingFSM.choosing_slot, F.data.startswith("slot_"))
async def slot_selected(callback: CallbackQuery, state: FSMContext):
    slot_id = int(callback.data.split("_")[1])
    user_data = await state.get_data()
    service_id = user_data.get("service_id")

    if service_id is None:
        await state.clear()
        await callback.message.edit_text(
            "⚠️ Сессия устарела. Пожалуйста, начните заново: /start"
        )
        await callback.answer()
        return

    async with async_session_maker() as session:
        repo = BookingRepository(session)
        await repo.get_or_create_user(
            user_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username,
        )
        success = await repo.book_slot_atomic(
            slot_id=slot_id,
            user_id=callback.from_user.id,
            service_id=service_id,
        )

    if success:
        await callback.message.edit_text(
            "✅ Вы успешно записаны! Мы уведомим вас накануне встречи."
        )
    else:
        await callback.message.edit_text(
            "⚠️ Это время уже успели забронировать. Пожалуйста, начните заново: /start"
        )

    await state.clear()
    await callback.answer()
