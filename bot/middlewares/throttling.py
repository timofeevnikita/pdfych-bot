from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    """
    Ограничивает частоту сообщений от одного пользователя (per-user rate limit)
    и глобальное количество одновременных обработок (global concurrent limit).
    """

    def __init__(
        self,
        user_rate: float = 1.0,
        global_max_concurrent: int = 10,
    ) -> None:
        self.user_rate = user_rate  # минимальный интервал между сообщениями (сек)
        self.global_max = global_max_concurrent
        self._user_last: dict[int, float] = {}
        self._active: int = 0

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        if user is None:
            return await handler(event, data)

        # Пропускаем rate limit для документов и фото — пользователь
        # может отправить несколько файлов подряд
        has_file = event.document is not None or event.photo is not None

        user_id = user.id
        now = time.monotonic()

        # Per-user rate limit (не для файлов)
        if not has_file:
            last = self._user_last.get(user_id, 0.0)
            if now - last < self.user_rate:
                await event.reply("⏳ Подожди пару секунд перед следующим запросом.")
                return None

        # Глобальный лимит одновременных обработок
        if self._active >= self.global_max:
            await event.reply("⚙️ Сервер сейчас занят. Попробуй через минуту.")
            return None

        self._user_last[user_id] = now
        self._active += 1
        try:
            return await handler(event, data)
        finally:
            self._active -= 1
