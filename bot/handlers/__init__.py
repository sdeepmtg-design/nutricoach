from aiogram import Router

from bot.handlers import chat, meal, menu, onboarding, payment, photo, start


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(onboarding.router)
    root.include_router(menu.router)
    root.include_router(photo.router)
    root.include_router(meal.router)
    root.include_router(chat.router)
    root.include_router(payment.router)
    return root
