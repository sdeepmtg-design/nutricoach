from bot.config import settings
from bot.database.db import db


async def check_photo_limit(user_id: int) -> tuple[bool, str]:
    user = await db.get_user(user_id)
    if not user:
        return False, "Сначала нажми /start"

    usage = await db.get_usage(user_id)
    is_pro = db.is_pro(user)

    day_limit = settings.pro_photos_per_day if is_pro else settings.free_photos_per_day
    month_limit = 0 if is_pro else settings.free_photos_per_month

    if usage["photos_today"] >= day_limit:
        if is_pro:
            return False, f"Достигнут дневной лимит ({day_limit} фото). Попробуй завтра."
        return False, (
            f"🚫 Лимит Free: {day_limit} фото/день.\n\n"
            "Оформи <b>Pro</b> — больше анализов, дневник и план на день.\n"
            "Нажми «⭐ Pro подписка» в меню."
        )

    if month_limit and usage["photos_month"] >= month_limit:
        return False, (
            f"🚫 Лимит Free: {month_limit} фото/месяц.\n\n"
            "Перейди на <b>Pro</b> для безлимитного месячного доступа."
        )

    return True, ""


async def check_ai_limit(user_id: int) -> tuple[bool, str]:
    user = await db.get_user(user_id)
    if not user:
        return False, "Сначала нажми /start"

    usage = await db.get_usage(user_id)
    is_pro = db.is_pro(user)
    limit = settings.pro_ai_messages_per_day if is_pro else settings.free_ai_messages_per_day

    if usage["ai_today"] >= limit:
        if is_pro:
            return False, f"Достигнут дневной лимит ({limit} сообщений)."
        return False, (
            f"🚫 Лимит Free: {limit} AI-вопросов/день.\n\n"
            "В <b>Pro</b> — до 100 консультаций и персональные программы."
        )

    return True, ""
