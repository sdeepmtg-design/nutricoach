from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import db
from bot.keyboards.inline import activity_kb, gender_kb, goal_kb, main_menu
from bot.services.nutrition import ACTIVITY_LABELS, GOAL_LABELS, calculate_targets
from bot.states import Onboarding

router = Router()


@router.callback_query(F.data.startswith("onboard:gender:"))
async def set_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.split(":")[-1]
    await state.update_data(gender=gender)
    await state.set_state(Onboarding.age)
    await callback.message.edit_text("Сколько тебе полных лет? (число)")
    await callback.answer()


@router.message(Onboarding.age)
async def set_age(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.isdigit():
        await message.answer("Введи возраст числом, например: 28")
        return
    age = int(message.text)
    if age < 14 or age > 100:
        await message.answer("Укажи возраст от 14 до 100")
        return
    await state.update_data(age=age)
    await state.set_state(Onboarding.height)
    await message.answer("Рост в см? (например: 175)")


@router.message(Onboarding.height)
async def set_height(message: Message, state: FSMContext) -> None:
    try:
        h = float(message.text.replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        await message.answer("Введи рост числом, например: 175")
        return
    if h < 120 or h > 230:
        await message.answer("Укажи рост от 120 до 230 см")
        return
    await state.update_data(height_cm=h)
    await state.set_state(Onboarding.weight)
    await message.answer("Текущий вес в кг? (например: 72.5)")


@router.message(Onboarding.weight)
async def set_weight(message: Message, state: FSMContext) -> None:
    try:
        w = float(message.text.replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        await message.answer("Введи вес числом")
        return
    if w < 35 or w > 250:
        await message.answer("Укажи вес от 35 до 250 кг")
        return
    await state.update_data(weight_kg=w)
    await state.set_state(Onboarding.activity)
    await message.answer("Уровень активности?", reply_markup=activity_kb())


@router.callback_query(F.data.startswith("onboard:activity:"))
async def set_activity(callback: CallbackQuery, state: FSMContext) -> None:
    activity = callback.data.split(":")[-1]
    await state.update_data(activity=activity)
    await state.set_state(Onboarding.goal)
    await callback.message.edit_text("Твоя цель?", reply_markup=goal_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("onboard:goal:"))
async def set_goal(callback: CallbackQuery, state: FSMContext) -> None:
    goal = callback.data.split(":")[-1]
    await state.update_data(goal=goal)
    if goal == "maintain":
        await finish_onboarding(callback, state)
    else:
        await state.set_state(Onboarding.target_weight)
        label = "желаемый" if goal == "lose" else "целевой"
        await callback.message.edit_text(f"Укажи {label} вес в кг:")
    await callback.answer()


@router.message(Onboarding.target_weight)
async def set_target_weight(message: Message, state: FSMContext) -> None:
    try:
        tw = float(message.text.replace(",", "."))
    except (TypeError, ValueError, AttributeError):
        await message.answer("Введи вес числом")
        return
    await state.update_data(target_weight_kg=tw)
    data = await state.get_data()
    # Fake callback finish via message
    user_id = message.from_user.id
    await _save_profile(user_id, {**data, "target_weight_kg": tw})
    await state.clear()
    user = await db.get_user(user_id)
    await message.answer(_profile_summary(user), reply_markup=main_menu(False))


async def finish_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    data.setdefault("target_weight_kg", data.get("weight_kg"))
    await _save_profile(callback.from_user.id, data)
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    await callback.message.edit_text(_profile_summary(user))
    await callback.message.answer("🏠 Меню:", reply_markup=main_menu(False))


async def _save_profile(user_id: int, data: dict) -> None:
    targets = calculate_targets(
        data["gender"],
        data["age"],
        data["height_cm"],
        data["weight_kg"],
        data["activity"],
        data["goal"],
    )
    await db.update_user(
        user_id,
        onboarding_done=1,
        gender=data["gender"],
        age=data["age"],
        height_cm=data["height_cm"],
        weight_kg=data["weight_kg"],
        activity=data["activity"],
        goal=data["goal"],
        target_weight_kg=data.get("target_weight_kg"),
        program=data["goal"],
        **targets,
    )


def _profile_summary(user: dict) -> str:
    return (
        "✅ <b>Профиль настроен!</b>\n\n"
        f"🎯 Цель: {GOAL_LABELS.get(user['goal'], user['goal'])}\n"
        f"🏃 Активность: {ACTIVITY_LABELS.get(user['activity'], user['activity'])}\n"
        f"📊 Норма: <b>{user['daily_calories']}</b> ккал\n"
        f"   Б: {user['daily_protein_g']}г | Ж: {user['daily_fat_g']}г | У: {user['daily_carbs_g']}г\n\n"
        "Отправь 📸 фото еды — получишь анализ за секунды!"
    )
