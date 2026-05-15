from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.db import db
from bot.keyboards.inline import main_menu
from bot.services.ai import nutrition_chat
from bot.services.limits import check_ai_limit
from bot.states import ChatState

router = Router()


@router.message(ChatState.waiting_question)
async def handle_chat(message: Message, state: FSMContext, db_user: dict) -> None:
    if not message.text:
        await message.answer("Напиши текстовый вопрос.")
        return

    ok, err = await check_ai_limit(message.from_user.id)
    if not ok:
        await message.answer(err)
        return

    thinking = await message.answer("🤔 Думаю...")
    answer = await nutrition_chat(db_user, message.text)
    await db.increment_usage(message.from_user.id, ai=1)
    await thinking.edit_text(f"💬 <b>NutriCoach:</b>\n\n{answer}")
    await state.clear()
    await message.answer("Ещё вопрос? Или меню:", reply_markup=main_menu(db.is_pro(db_user)))
