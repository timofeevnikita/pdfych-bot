from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_pdf_format_keyboard(file_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора формата конвертации PDF-файла."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Word (.docx)", callback_data=f"convert:docx:{file_id}")
    builder.button(text="🖼 Картинки (.jpg)", callback_data=f"convert:jpg:{file_id}")
    builder.button(text="❌ Отмена", callback_data=f"convert:cancel:{file_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_merge_action_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения склейки PDF."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📎 Склеить PDF", callback_data="merge:done")
    builder.button(text="❌ Отмена", callback_data="merge:cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_split_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения разделения PDF."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✂️ Разделить", callback_data="split:confirm")
    builder.button(text="❌ Отмена", callback_data="split:cancel")
    builder.adjust(2)
    return builder.as_markup()
