from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Optional

from aiogram import Bot
from aiogram.types import File

from bot.config import config
from bot.utils.helpers import safe_filename

logger = logging.getLogger(__name__)


async def download_file(bot: Bot, file_id: str, extension: str) -> str:
    """Скачивает файл из Telegram и сохраняет под UUID-именем. Возвращает путь."""
    os.makedirs(config.TMP_DIR, exist_ok=True)

    filename = safe_filename(extension)
    dest_path = os.path.join(config.TMP_DIR, filename)

    tg_file: File = await bot.get_file(file_id)
    await bot.download_file(tg_file.file_path, destination=dest_path)

    logger.debug("Downloaded file %s → %s", file_id, dest_path)
    return dest_path


async def cleanup_old_files(tmp_dir: str, max_age_seconds: int) -> None:
    """Удаляет файлы старше max_age_seconds секунд из tmp-директории."""
    if not os.path.isdir(tmp_dir):
        return

    now = time.time()
    removed = 0

    for filename in os.listdir(tmp_dir):
        filepath = os.path.join(tmp_dir, filename)
        if not os.path.isfile(filepath):
            continue
        try:
            age = now - os.path.getmtime(filepath)
            if age > max_age_seconds:
                os.remove(filepath)
                removed += 1
        except OSError:
            pass

    if removed:
        logger.debug("Cleanup: removed %d old file(s) from %s", removed, tmp_dir)


async def safe_remove(*paths: Optional[str]) -> None:
    """Безопасно удаляет один или несколько файлов (игнорирует ошибки)."""
    for path in paths:
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


async def safe_remove_list(paths: list[str]) -> None:
    """Безопасно удаляет список файлов."""
    for path in paths:
        if path and os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
