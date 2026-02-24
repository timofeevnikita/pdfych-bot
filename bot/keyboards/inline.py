from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_pdf_format_keyboard(key: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора формата конвертации PDF-файла."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Word (.docx)",
                    callback_data=f"convert:docx:{key}",
                ),
                InlineKeyboardButton(
                    text="Картинки (.jpg)",
                    callback_data=f"convert:jpg:{key}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=f"convert:cancel:{key}",
                ),
            ],
        ]
    )


def get_merge_action_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения склейки PDF."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Склеить PDF", callback_data="merge:done"),
                InlineKeyboardButton(text="Отмена", callback_data="merge:cancel"),
            ],
        ]
    )


def get_split_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения разделения PDF."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Разделить", callback_data="split:confirm"),
                InlineKeyboardButton(text="Отмена", callback_data="split:cancel"),
            ],
        ]
    )
