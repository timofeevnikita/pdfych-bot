from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.database.db import upsert_user

logger = logging.getLogger(__name__)


class UserLoggingMiddleware(BaseMiddleware):
    """
    При каждом входящем сообщении создаёт/обновляет запись пользователя в БД.
    """

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user is not None:
            try:
                await upsert_user(user.id, user.username, user.first_name)
            except Exception:
                logger.exception(
                    "UserLoggingMiddleware: не удалось сохранить пользователя %s",
                    user.id,
                )
        return await handler(event, data)
