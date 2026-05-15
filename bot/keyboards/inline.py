from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import settings


def main_menu(is_pro: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📸 Анализ по фото", callback_data="menu:photo"),
        InlineKeyboardButton(text="📝 Описать еду", callback_data="menu:text_meal"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 План на день", callback_data="menu:day"),
        InlineKeyboardButton(text="📈 Итоги недели", callback_data="menu:week"),
    )
    builder.row(
        InlineKeyboardButton(text="💬 Спросить нутрициолога", callback_data="menu:chat"),
        InlineKeyboardButton(text="⚖️ Записать вес", callback_data="menu:weight"),
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
        InlineKeyboardButton(
            text="⭐ Pro" if not is_pro else "⭐ Pro активен",
            callback_data="menu:pro",
        ),
    )
    return builder.as_markup()


def gender_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужской", callback_data="onboard:gender:male"),
                InlineKeyboardButton(text="👩 Женский", callback_data="onboard:gender:female"),
            ]
        ]
    )


def activity_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🪑 Сидячий", callback_data="onboard:activity:sedentary")],
            [InlineKeyboardButton(text="🚶 Лёгкая", callback_data="onboard:activity:light")],
            [InlineKeyboardButton(text="🏃 Умеренная", callback_data="onboard:activity:moderate")],
            [InlineKeyboardButton(text="💪 Высокая", callback_data="onboard:activity:active")],
            [InlineKeyboardButton(text="🔥 Очень высокая", callback_data="onboard:activity:very_active")],
        ]
    )


def goal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📉 Похудение", callback_data="onboard:goal:lose")],
            [InlineKeyboardButton(text="⚖️ Поддержание", callback_data="onboard:goal:maintain")],
            [InlineKeyboardButton(text="📈 Набор массы", callback_data="onboard:goal:gain")],
        ]
    )


def meal_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌅 Завтрак", callback_data="meal:type:breakfast"),
                InlineKeyboardButton(text="☀️ Обед", callback_data="meal:type:lunch"),
            ],
            [
                InlineKeyboardButton(text="🌙 Ужин", callback_data="meal:type:dinner"),
                InlineKeyboardButton(text="🍎 Перекус", callback_data="meal:type:snack"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="meal:cancel")],
        ]
    )


def save_meal_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💾 Сохранить в дневник", callback_data="meal:save"),
                InlineKeyboardButton(text="🗑 Не сохранять", callback_data="meal:skip"),
            ]
        ]
    )


def pro_plans_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"⭐ Pro месяц — {settings.pro_month_stars} ⭐",
                    callback_data="pay:month",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"⭐ Pro год — {settings.pro_year_stars} ⭐ (выгоднее)",
                    callback_data="pay:year",
                )
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
        ]
    )


def back_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:back")]]
    )
