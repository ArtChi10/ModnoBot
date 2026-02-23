import logging
from asyncio import run

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import get_settings
from bot.handlers.command import router as commands_router
from bot.handlers.errors import router as error_router
from bot.internal.enums import Stage
from bot.internal.helpers import setup_logs
from bot.internal.notify_admin import on_shutdown, on_startup
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.logging import LoggingMiddleware
from bot.middlewares.session import DBSessionMiddleware
from bot.middlewares.updates_dumper import UpdatesDumperMiddleware
from bot.middlewares.user_limit import UserLimitMiddleware
from database.database_connector import get_db


async def main() -> None:
    setup_logs("suslik_robot")
    settings = get_settings()
    if settings.bot.SENTRY_DSN and settings.bot.STAGE == Stage.PROD:
        sentry_sdk.init(
            dsn=settings.bot.SENTRY_DSN.get_secret_value(),
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
    bot = Bot(
        token=settings.bot.TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    redis_client = Redis(
        host=settings.redis.HOST,
        port=settings.redis.PORT,
        username=settings.redis.USERNAME,
        password=settings.redis.PASSWORD.get_secret_value(),
        decode_responses=True,
    )
    storage = RedisStorage(redis_client)
    dispatcher = Dispatcher(storage=storage, settings=settings)
    db = get_db(settings)
    await db.init_models()
    db_session_middleware = DBSessionMiddleware(db)
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(on_startup)
    dispatcher.shutdown.register(on_shutdown)
    dispatcher.message.middleware(db_session_middleware)
    dispatcher.callback_query.middleware(db_session_middleware)
    dispatcher.message.middleware(AuthMiddleware())
    dispatcher.callback_query.middleware(AuthMiddleware())
    dispatcher.update.middleware(UserLimitMiddleware())
    dispatcher.message.middleware.register(LoggingMiddleware())
    dispatcher.callback_query.middleware.register(LoggingMiddleware())
    dispatcher.include_routers(commands_router, error_router)
    logging.info("suslik robot started")
    await dispatcher.start_polling(bot, skip_updates=True)


def run_main() -> None:
    run(main())


if __name__ == "__main__":
    run_main()
