from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.database.db import db
from bot.keyboards.inline import main_menu, meal_type_kb, save_meal_kb
from bot.services.ai import analyze_food_photo
from bot.services.limits import check_photo_limit
from bot.services.nutrition import day_summary
from bot.states import MealInput

router = Router()

CONFIDENCE_EMOJI = {"high": "🟢", "medium": "🟡", "low": "🔴"}


def format_analysis(data: dict) -> str:
    conf = data.get("confidence", "medium")
    emoji = CONFIDENCE_EMOJI.get(conf, "🟡")
    return (
        f"🍽 <b>{data.get('description', 'Блюдо')}</b>\n\n"
        f"📊 <b>Оценка:</b>\n"
        f"• Калории: <b>{data.get('calories', 0)}</b> ккал\n"
        f"• Б: {data.get('protein_g', 0)} г | Ж: {data.get('fat_g', 0)} г | "
        f"У: {data.get('carbs_g', 0)} г\n\n"
        f"{emoji} Уверенность: <b>{conf}</b>\n"
        f"<i>{data.get('assumptions', '')}</i>\n\n"
        f"✅ <b>Хорошо:</b> {data.get('tips_good', '—')}\n"
        f"⚠️ <b>Ограничить:</b> {data.get('tips_limit', '—')}"
    )


@router.message(F.photo)
async def handle_photo(message: Message, state: FSMContext, db_user: dict) -> None:
    if not db_user.get("onboarding_done"):
        await message.answer("Сначала заверши настройку: /start")
        return

    ok, err = await check_photo_limit(message.from_user.id)
    if not ok:
        await message.answer(err)
        return

    status = await message.answer("🔍 Анализирую фото...")

    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    downloaded = await message.bot.download_file(file.file_path)
    image_bytes = downloaded.read()

    result = await analyze_food_photo(image_bytes)
    if not result:
        await status.edit_text("❌ Не удалось распознать. Попробуй другое фото.")
        return

    await db.increment_usage(message.from_user.id, photos=1)

    await state.update_data(pending_meal=result, pending_meal_type="lunch")

    text = format_analysis(result)
    is_pro = db.is_pro(db_user)

    if is_pro:
        await status.edit_text(
            text + "\n\nВыбери тип приёма для сохранения:",
            reply_markup=meal_type_kb(),
        )
        await state.set_state(MealInput.waiting_type)
    else:
        await status.edit_text(
            text + "\n\n<i>Дневник питания — в Pro ⭐. Нажми «Pro» в меню.</i>",
            reply_markup=main_menu(False),
        )
