from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.database.db import db
from bot.keyboards.inline import gender_kb, main_menu

router = Router()

WELCOME = """🥗 <b>Добро пожаловать в NutriCoach!</b>

Твой AI-нутрициолог в Telegram:
• 📸 Калории и БЖУ по фото за 10 секунд
• 📊 План на день с прогресс-баром
• 💬 Персональные советы 24/7
• 📈 Итоги недели и дневник веса

<b>Free:</b> {free_photos} фото/день, {free_ai} AI-вопросов
<b>Pro:</b> дневник, программы, безлимитный месяц — от {stars} ⭐/мес

Отправь фото еды или выбери действие в меню 👇"""


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: dict) -> None:
    from bot.config import settings

    if not db_user.get("onboarding_done"):
        await message.answer(
            "👋 Привет! Давай настроим профиль — займёт 1 минуту.\n\nКакой у тебя пол?",
            reply_markup=gender_kb(),
        )
        return

    is_pro = db.is_pro(db_user)
    await message.answer(
        WELCOME.format(
            free_photos=settings.free_photos_per_day,
            free_ai=settings.free_ai_messages_per_day,
            stars=settings.pro_month_stars,
        ),
        reply_markup=main_menu(is_pro),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, db_user: dict) -> None:
    is_pro = db.is_pro(db_user)
    await message.answer("🏠 <b>Главное меню</b>", reply_markup=main_menu(is_pro))
