from __future__ import annotations

import logging
import os
from typing import Optional

import aiosqlite

from bot.database.models import ALL_MIGRATIONS

logger = logging.getLogger(__name__)

_db: Optional[aiosqlite.Connection] = None


async def init_db(db_path: str) -> None:
    """Инициализирует БД: создаёт файл и все таблицы."""
    global _db

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    _db = await aiosqlite.connect(db_path)
    _db.row_factory = aiosqlite.Row

    for migration in ALL_MIGRATIONS:
        await _db.execute(migration)
    await _db.commit()

    logger.info("Database initialized: %s", db_path)


async def _get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("База данных не инициализирована. Вызовите init_db() при старте.")
    return _db


async def upsert_user(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
) -> None:
    """Создаёт или обновляет запись пользователя."""
    db = await _get_db()
    await db.execute(
        """
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username   = excluded.username,
            first_name = excluded.first_name
        """,
        (user_id, username, first_name),
    )
    await db.commit()


async def log_conversion(
    user_id: int,
    input_format: str,
    output_format: str,
    file_size: Optional[int],
    success: bool,
) -> None:
    """Записывает результат конвертации в историю."""
    db = await _get_db()
    await db.execute(
        """
        INSERT INTO conversions (user_id, input_format, output_format, file_size, success)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, input_format, output_format, file_size, 1 if success else 0),
    )
    await db.commit()


async def check_daily_limit(user_id: int, limit: int) -> bool:
    """Возвращает True если пользователь НЕ превысил дневной лимит."""
    db = await _get_db()
    async with db.execute(
        """
        SELECT COUNT(*) FROM conversions
        WHERE user_id = ?
          AND success = 1
          AND created_at >= datetime('now', '-1 day')
        """,
        (user_id,),
    ) as cursor:
        row = await cursor.fetchone()
        count = row[0] if row else 0
    return count < limit


async def close_db() -> None:
    """Закрывает соединение с БД. Вызывать при завершении бота."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
