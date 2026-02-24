from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.database.db import close_db, init_db
from bot.handlers import convert, merge_pdf, settings, split_pdf, start
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.middlewares.user_logging import UserLoggingMiddleware
from bot.services.file_manager import cleanup_old_files


async def periodic_cleanup(tmp_dir: str, max_age: int) -> None:
    """Фоновая задача: удаляет старые временные файлы каждые 60 секунд."""
    while True:
        await asyncio.sleep(60)
        try:
            await cleanup_old_files(tmp_dir, max_age)
        except Exception:
            logging.getLogger(__name__).exception("Ошибка при очистке tmp")


async def main() -> None:
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Создаём нужные директории
    os.makedirs(config.TMP_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(config.DB_PATH)), exist_ok=True)

    # Инициализируем БД
    await init_db(config.DB_PATH)

    # Создаём бота и диспетчер
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Регистрируем middleware (порядок важен: throttling → logging)
    dp.message.middleware(ThrottlingMiddleware(user_rate=1.0, global_max_concurrent=10))
    dp.message.middleware(UserLoggingMiddleware())

    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(convert.router)
    dp.include_router(merge_pdf.router)
    dp.include_router(split_pdf.router)
    dp.include_router(settings.router)

    # Запускаем фоновую очистку tmp
    asyncio.create_task(periodic_cleanup(config.TMP_DIR, config.TMP_MAX_AGE_SECONDS))

    logger.info("ПДФыч bot starting...")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()
        logger.info("ПДФыч bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
