from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

SETTINGS_TEXT = """
⚙️ <b>Настройки ПДФыч</b>

На данный момент все настройки применяются автоматически.

<b>Текущие параметры:</b>
• Язык интерфейса: Русский 🇷🇺
• Качество JPG при конвертации PDF: 150 DPI
• Временные файлы удаляются автоматически через 5 минут
""".strip()


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await message.answer(SETTINGS_TEXT)
