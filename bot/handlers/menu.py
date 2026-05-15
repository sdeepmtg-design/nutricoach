from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import db
from bot.keyboards.inline import back_menu_kb, main_menu, meal_type_kb, pro_plans_kb
from bot.services.nutrition import day_summary, week_insights
from bot.states import ChatState, MealInput, WeightInput

router = Router()

PRO_FEATURES = """⭐ <b>NutriCoach Pro</b>

<b>Что даёт Pro</b> (конкуренты берут 199–490₽, мы — Stars):
✅ Сохранение приёмов пищи и дневник
✅ План на день: остаток ккал, «утечки»
✅ Итоги недели с инсайтами
✅ Дневник веса
✅ Программы: похудение / набор / поддержание
✅ До 50 фото и 100 AI-вопросов в день

<b>Free:</b> 3 фото/день, 30/мес, 5 AI-вопросов

Оплата через Telegram Stars ⭐ — без карт и сайтов."""


@router.callback_query(F.data == "menu:back")
async def menu_back(callback: CallbackQuery, db_user: dict) -> None:
    is_pro = db.is_pro(db_user)
    await callback.message.edit_text("🏠 <b>Главное меню</b>", reply_markup=main_menu(is_pro))
    await callback.answer()


@router.callback_query(F.data == "menu:day")
async def menu_day(callback: CallbackQuery, db_user: dict) -> None:
    if not db_user.get("onboarding_done"):
        await callback.answer("Сначала /start", show_alert=True)
        return
    meals = await db.get_meals_today(callback.from_user.id)
    text = day_summary(meals, db_user)
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:week")
async def menu_week(callback: CallbackQuery, db_user: dict) -> None:
    if not db.is_pro(db_user):
        await callback.answer("Итоги недели — функция Pro ⭐", show_alert=True)
        return
    meals = await db.get_meals_week(callback.from_user.id)
    text = week_insights(meals, db_user)
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:profile")
async def menu_profile(callback: CallbackQuery, db_user: dict) -> None:
    from bot.services.nutrition import ACTIVITY_LABELS, GOAL_LABELS

    pro = "⭐ Pro до " + db_user["pro_until"][:10] if db.is_pro(db_user) else "Free"
    usage = await db.get_usage(callback.from_user.id)
    text = (
        f"👤 <b>Профиль</b> ({pro})\n\n"
        f"Пол: {'Ж' if db_user.get('gender') == 'female' else 'М'}, "
        f"{db_user.get('age')} лет\n"
        f"Рост: {db_user.get('height_cm')} см, вес: {db_user.get('weight_kg')} кг\n"
        f"Цель: {GOAL_LABELS.get(db_user.get('goal', ''), '?')}\n"
        f"Норма: {db_user.get('daily_calories')} ккал\n\n"
        f"Сегодня: 📸 {usage['photos_today']} фото, "
        f"💬 {usage['ai_today']} AI"
    )
    history = await db.get_weight_history(callback.from_user.id, 5)
    if history:
        text += "\n\n<b>Вес (последние):</b>\n"
        for h in history[-5:]:
            text += f"• {h['created_at'][:10]}: {h['weight_kg']} кг\n"
    await callback.message.edit_text(text, reply_markup=back_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:pro")
async def menu_pro(callback: CallbackQuery, db_user: dict) -> None:
    if db.is_pro(db_user):
        await callback.message.edit_text(
            f"✅ <b>Pro активен</b> до {db_user['pro_until'][:10]}\n\n" + PRO_FEATURES,
            reply_markup=back_menu_kb(),
        )
    else:
        await callback.message.edit_text(PRO_FEATURES, reply_markup=pro_plans_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:photo")
async def menu_photo_hint(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "📸 Отправь фото блюда в этот чат.\n\n"
        "Совет: снимай сверху, чтобы было видно всю порцию."
    )


@router.callback_query(F.data == "menu:text_meal")
async def menu_text_meal(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(MealInput.waiting_type)
    await callback.message.edit_text("Выбери тип приёма пищи:", reply_markup=meal_type_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:weight")
async def menu_weight(callback: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    if not db.is_pro(db_user):
        await callback.answer("Дневник веса — функция Pro ⭐", show_alert=True)
        return
    await state.set_state(WeightInput.waiting_weight)
    await callback.message.edit_text("Введи текущий вес в кг (например: 71.2):")
    await callback.answer()


@router.callback_query(F.data == "menu:chat")
async def menu_chat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ChatState.waiting_question)
    await callback.message.edit_text(
        "💬 Задай вопрос нутрициологу (например: «чем заменить сладкое на вечер?»):",
        reply_markup=back_menu_kb(),
    )
    await callback.answer()


@router.message(WeightInput.waiting_weight)
async def save_weight(message: Message, state: FSMContext, db_user: dict) -> None:
    try:
        w = float(message.text.replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        await message.answer("Введи вес числом")
        return
    await db.log_weight(message.from_user.id, w)
    await state.clear()
    is_pro = db.is_pro(db_user)
    await message.answer(f"✅ Вес {w} кг записан!", reply_markup=main_menu(is_pro))
