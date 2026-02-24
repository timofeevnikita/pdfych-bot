from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import config
from bot.keyboards.inline import get_split_confirm_keyboard
from bot.services.converter import do_split
from bot.services.file_manager import download_file, safe_remove, safe_remove_list
from bot.services.pdf_tools import get_pdf_page_count
from bot.utils.helpers import get_extension, human_readable_size, validate_file

logger = logging.getLogger(__name__)

router = Router()

_PAGE_SEND_DELAY = 0.15  # задержка между отправкой страниц (сек)


class SplitStates(StatesGroup):
    waiting_pdf = State()   # ждём PDF для разделения
    confirming = State()    # ждём подтверждения от пользователя


@router.message(Command("split"))
async def cmd_split(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SplitStates.waiting_pdf)

    await message.answer(
        "✂️ <b>Режим разделения PDF</b>\n\n"
        "Отправь PDF-файл, который нужно разбить на отдельные страницы.\n\n"
        "Каждая страница будет отправлена отдельным файлом."
    )


@router.message(SplitStates.waiting_pdf, F.document)
async def receive_split_pdf(message: Message, bot: Bot, state: FSMContext) -> None:
    doc = message.document
    if doc is None:
        return

    # Проверяем что файл — PDF
    ext = get_extension(doc.file_name, doc.mime_type)
    if ext != ".pdf":
        await message.reply("❌ Нужен PDF-файл. Отправь документ в формате .pdf")
        return

    # Проверяем размер
    if doc.file_size and doc.file_size > config.max_file_size_bytes:
        await message.reply(
            f"❌ Файл слишком большой. Максимум: {config.MAX_FILE_SIZE_MB} МБ."
        )
        return

    # Скачиваем
    try:
        path = await download_file(bot, doc.file_id, ".pdf")
    except Exception:
        logger.exception("split: download failed for user %s", message.from_user.id)
        await message.reply("❌ Не удалось скачать файл. Попробуй ещё раз.")
        return

    # Проверяем MIME
    if not validate_file(path, ".pdf"):
        await safe_remove(path)
        await message.reply("❌ Файл не является PDF. Отправь корректный PDF.")
        return

    # Считаем страницы
    try:
        page_count = get_pdf_page_count(path)
    except Exception:
        await safe_remove(path)
        await message.reply("❌ Не удалось прочитать PDF. Файл может быть повреждён.")
        return

    display_name = doc.file_name or "document.pdf"
    size_str = human_readable_size(doc.file_size or 0)

    await state.update_data(
        pdf_path=path,
        page_count=page_count,
        file_name=display_name,
    )
    await state.set_state(SplitStates.confirming)

    await message.reply(
        f"📄 Файл: <b>{display_name}</b> ({size_str})\n"
        f"Страниц: <b>{page_count}</b>\n\n"
        "Разделить на отдельные страницы?",
        reply_markup=get_split_confirm_keyboard(),
    )


@router.message(SplitStates.waiting_pdf)
async def split_waiting_unknown(message: Message) -> None:
    await message.reply("✂️ Жду PDF-файл для разделения. Отправь документ.")


@router.callback_query(F.data == "split:confirm", SplitStates.confirming)
async def handle_split_confirm(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    await callback.answer()

    data = await state.get_data()
    pdf_path: str = data["pdf_path"]
    page_count: int = data["page_count"]

    await state.clear()

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    status_msg = await callback.message.answer(
        f"⏳ Разделяю {page_count} страниц..."
    )
    output_paths: list[str] = []

    try:
        output_paths = await do_split(pdf_path)
        total = len(output_paths)

        for i, path in enumerate(output_paths):
            page_num = i + 1
            fname = f"page_{page_num:03d}.pdf"
            result_file = FSInputFile(path, filename=fname)
            caption = f"✅ Готово: {total} страниц — ПДФыч" if page_num == total else None
            await callback.message.answer_document(result_file, caption=caption)
            if i < total - 1:
                await asyncio.sleep(_PAGE_SEND_DELAY)

    except ValueError as e:
        logger.warning("Split ValueError user=%s: %s", callback.from_user.id, e)
        await callback.message.answer(f"❌ {e}")
    except Exception:
        logger.exception("Split failed: user=%s", callback.from_user.id)
        await callback.message.answer(
            "❌ Не удалось разделить PDF. Проверь, что файл не повреждён."
        )
    finally:
        await safe_remove(pdf_path)
        await safe_remove_list(output_paths)
        try:
            await status_msg.delete()
        except Exception:
            pass


@router.callback_query(F.data == "split:cancel", SplitStates.confirming)
async def handle_split_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()

    data = await state.get_data()
    pdf_path: Optional[str] = data.get("pdf_path")
    await state.clear()

    await safe_remove(pdf_path)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer("❌ Разделение отменено.")
