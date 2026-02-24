from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from bot.config import config

router = Router()

START_TEXT = """
🔄 <b>ПДФыч</b> — мгновенный конвертер файлов

Просто отправь мне документ — я конвертирую его за секунды.

📄 <b>Что умею:</b>
• Word, Excel, PowerPoint → PDF
• PDF → Word (.docx)
• PDF → картинки (постранично, .jpg)
• Картинки (JPG, PNG, WEBP, HEIC) → PDF
• Несколько фото → один PDF
• Склейка нескольких PDF → один файл
• Разделение PDF на отдельные страницы

📎 Отправь файл прямо сейчас или выбери команду:
/merge — склеить несколько PDF
/split — разделить PDF на страницы
/help — подробная справка
""".strip()

HELP_TEXT = """
📖 <b>Справка ПДФыч</b>

<b>Поддерживаемые форматы:</b>
• <code>.doc</code>, <code>.docx</code> — Microsoft Word → PDF
• <code>.xls</code>, <code>.xlsx</code> — Microsoft Excel → PDF
• <code>.ppt</code>, <code>.pptx</code> — Microsoft PowerPoint → PDF
• <code>.jpg</code>, <code>.png</code>, <code>.webp</code>, <code>.heic</code> — картинки → PDF
• Несколько фото одним альбомом → один PDF
• <code>.pdf</code> → Word (.docx) или картинки (.jpg)

<b>Ограничения:</b>
• Максимальный размер файла: <b>{max_mb} МБ</b>
• Дневной лимит: <b>{daily} конвертаций</b>

<b>Как использовать:</b>
Просто отправь файл — бот определит формат и предложит варианты конвертации.
Отправь несколько фото одним альбомом — получишь один PDF.
""".strip()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(START_TEXT, reply_markup=ReplyKeyboardRemove())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = HELP_TEXT.format(
        max_mb=config.MAX_FILE_SIZE_MB,
        daily=config.FREE_DAILY_LIMIT,
    )
    await message.answer(text)
