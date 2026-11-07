from aiogram.fsm.state import State, StatesGroup


class BookingFSM(StatesGroup):
    choosing_service = State()
    choosing_slot = State()
    confirming = State()
