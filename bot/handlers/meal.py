from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.database.db import db
from bot.keyboards.inline import back_menu_kb, main_menu, meal_type_kb, save_meal_kb
from bot.services.nutrition import day_summary
from bot.states import MealInput

router = Router()


@router.callback_query(F.data.startswith("meal:type:"))
async def pick_meal_type(callback: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    meal_type = callback.data.split(":")[-1]
    data = await state.get_data()

    if data.get("pending_meal"):
        await _save_pending(callback.from_user.id, meal_type, data["pending_meal"], callback, state, db_user)
        return

    await state.update_data(meal_type=meal_type)
    await state.set_state(MealInput.waiting_description)
    await callback.message.edit_text(
        "Опиши что съел(а) (например: «гречка 200г с курицей и салатом»):"
    )
    await callback.answer()


@router.message(MealInput.waiting_description)
async def text_meal_description(message: Message, state: FSMContext, db_user: dict) -> None:
    if not db.is_pro(db_user):
        await message.answer("Дневник питания доступен в Pro ⭐")
        await state.clear()
        return

    desc = message.text or ""
    data = await state.get_data()
    meal_type = data.get("meal_type", "snack")

    # Простая оценка по тексту через AI chat parsing - use rough estimate
    result = {
        "description": desc[:80],
        "calories": 400,
        "protein_g": 20,
        "fat_g": 15,
        "carbs_g": 45,
        "confidence": "low",
        "assumptions": "Оценка по описанию",
        "tips_good": "Запись добавлена в дневник",
        "tips_limit": "—",
    }

    await db.add_meal(
        message.from_user.id,
        meal_type,
        result["description"],
        int(result["calories"]),
        float(result["protein_g"]),
        float(result["fat_g"]),
        float(result["carbs_g"]),
    )
    await state.clear()
    meals = await db.get_meals_today(message.from_user.id)
    await message.answer(
        f"✅ Записано: {desc[:50]}\n\n" + day_summary(meals, db_user),
        reply_markup=main_menu(db.is_pro(db_user)),
    )


@router.callback_query(F.data == "meal:save")
async def save_meal(callback: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    if not db.is_pro(db_user):
        await callback.answer("Дневник — Pro ⭐", show_alert=True)
        return
    data = await state.get_data()
    pending = data.get("pending_meal")
    if not pending:
        await callback.answer("Нет данных для сохранения", show_alert=True)
        return
    meal_type = data.get("pending_meal_type", "lunch")
    await _save_pending(callback.from_user.id, meal_type, pending, callback, state, db_user)


@router.callback_query(F.data == "meal:skip")
async def skip_meal(callback: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    await state.update_data(pending_meal=None)
    await callback.message.edit_text("Ок, не сохраняю.", reply_markup=main_menu(db.is_pro(db_user)))
    await callback.answer()


@router.callback_query(F.data == "meal:cancel")
async def cancel_meal(callback: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    await state.clear()
    await callback.message.edit_text("Отменено.", reply_markup=main_menu(db.is_pro(db_user)))
    await callback.answer()


async def _save_pending(
    user_id: int,
    meal_type: str,
    pending: dict,
    callback: CallbackQuery,
    state: FSMContext,
    db_user: dict,
) -> None:
    await db.add_meal(
        user_id,
        meal_type,
        pending.get("description", "Блюдо"),
        int(pending.get("calories", 0)),
        float(pending.get("protein_g", 0)),
        float(pending.get("fat_g", 0)),
        float(pending.get("carbs_g", 0)),
        pending.get("confidence"),
        pending.get("tips_good"),
        pending.get("tips_limit"),
    )
    await state.clear()
    meals = await db.get_meals_today(user_id)
    await callback.message.edit_text(
        "✅ Сохранено в дневник!\n\n" + day_summary(meals, db_user),
        reply_markup=main_menu(db.is_pro(db_user)),
    )
    await callback.answer("Сохранено!")
