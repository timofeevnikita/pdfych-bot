from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.keyboards.inline import get_start_keyboard

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

📎 Отправь файл прямо сейчас или выбери действие:
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

<b>Команды:</b>
/merge — склейка нескольких PDF в один
/split — разделить PDF на отдельные страницы
/help — эта справка

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
    await message.answer(START_TEXT, reply_markup=get_start_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = HELP_TEXT.format(
        max_mb=config.MAX_FILE_SIZE_MB,
        daily=config.FREE_DAILY_LIMIT,
    )
    await message.answer(text)


@router.callback_query(F.data == "menu:merge")
async def menu_merge(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка «Склеить PDF» из главного меню."""
    await callback.answer()
    # Импортируем здесь, чтобы избежать циклического импорта
    from bot.handlers.merge_pdf import cmd_merge
    await cmd_merge(callback.message, state)


@router.callback_query(F.data == "menu:split")
async def menu_split(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка «Разделить PDF» из главного меню."""
    await callback.answer()
    from bot.handlers.split_pdf import cmd_split
    await cmd_split(callback.message, state)


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery) -> None:
    """Кнопка «Справка» из главного меню."""
    await callback.answer()
    text = HELP_TEXT.format(
        max_mb=config.MAX_FILE_SIZE_MB,
        daily=config.FREE_DAILY_LIMIT,
    )
    await callback.message.answer(text)
