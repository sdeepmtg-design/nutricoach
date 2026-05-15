from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from bot.config import settings
from bot.database.db import db
from bot.keyboards.inline import main_menu

router = Router()

PLANS = {
    "month": {"days": 30, "stars": settings.pro_month_stars, "title": "NutriCoach Pro — 1 месяц"},
    "year": {"days": 365, "stars": settings.pro_year_stars, "title": "NutriCoach Pro — 1 год"},
}


@router.callback_query(F.data.startswith("pay:"))
async def send_invoice(callback: CallbackQuery) -> None:
    plan_key = callback.data.split(":")[-1]
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неизвестный тариф", show_alert=True)
        return

    await callback.message.answer_invoice(
        title=plan["title"],
        description=(
            "Дневник питания, план на день, итоги недели, дневник веса, "
            "программы похудения/набора, расширенные лимиты AI и фото."
        ),
        payload=f"pro_{plan_key}",
        currency="XTR",
        prices=[LabeledPrice(label=plan["title"], amount=plan["stars"])],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment
    payload = payment.invoice_payload or ""
    plan_key = payload.replace("pro_", "")
    plan = PLANS.get(plan_key, PLANS["month"])

    await db.activate_pro(message.from_user.id, plan["days"])
    await db.record_payment(
        message.from_user.id,
        plan_key,
        payment.total_amount,
        payment.telegram_payment_charge_id,
    )

    user = await db.get_user(message.from_user.id)
    await message.answer(
        f"🎉 <b>Спасибо за оплату!</b>\n\n"
        f"Pro активирован на {plan['days']} дней.\n"
        f"Действует до: {user['pro_until'][:10]}\n\n"
        "Теперь доступны: дневник, итоги недели, вес и сохранение фото.",
        reply_markup=main_menu(True),
    )
