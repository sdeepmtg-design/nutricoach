import asyncio
import logging
import sys

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from bot.config import settings
from bot.database.db import db
from bot.handlers import setup_routers
from bot.middlewares.user import UserMiddleware

WEBHOOK_PATH = "/webhook"
logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.include_router(setup_routers())
    return dp


async def init_database() -> None:
    conn = await db.connect()
    await conn.close()


async def on_startup(bot: Bot) -> None:
    await init_database()
    url = f"{settings.webhook_url}{WEBHOOK_PATH}"
    await bot.set_webhook(url, secret_token=settings.webhook_secret)
    logger.info("NutriCoach webhook: %s", url)


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=False)
    await bot.session.close()


async def run_polling() -> None:
    await init_database()
    bot = create_bot()
    dp = create_dispatcher()
    logger.info("NutriCoach polling started")
    await dp.start_polling(bot)


def run_webhook() -> None:
    bot = create_bot()
    dp = create_dispatcher()

    app = web.Application()

    async def health(_request: web.Request) -> web.Response:
        return web.Response(text="ok")

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret,
    )
    webhook_handler.register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)

    logger.info("NutriCoach web server on 0.0.0.0:%s", settings.port)
    web.run_app(app, host="0.0.0.0", port=settings.port)


def main() -> None:
    if not settings.bot_token:
        print("Укажи BOT_TOKEN в переменных окружения")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO)

    if settings.bot_mode == "webhook":
        if not settings.webhook_url:
            print(
                "Для webhook укажи WEBHOOK_URL или задеплой на Render "
                "(используется RENDER_EXTERNAL_URL)"
            )
            sys.exit(1)
        run_webhook()
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
