from __future__ import annotations

import logging
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import config
from bot.keyboards.inline import get_merge_action_keyboard
from bot.services.converter import do_merge
from bot.services.file_manager import download_file, safe_remove, safe_remove_list
from bot.utils.helpers import get_extension, validate_file

logger = logging.getLogger(__name__)

router = Router()

MAX_MERGE_FILES = 10  # максимум PDF для склейки


class MergeStates(StatesGroup):
    collecting = State()  # собираем PDF-файлы


@router.message(Command("merge"))
async def cmd_merge(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MergeStates.collecting)
    await state.update_data(pdf_paths=[], pdf_count=0)

    await message.answer(
        "📎 <b>Режим склейки PDF</b>\n\n"
        "Отправляй PDF-файлы один за другим.\n"
        f"Максимум: <b>{MAX_MERGE_FILES} файлов</b>.\n\n"
        "Когда добавишь все — нажми <b>«Склеить PDF»</b>.",
        reply_markup=get_merge_action_keyboard(),
    )


@router.message(MergeStates.collecting, F.document)
async def collect_pdf(message: Message, bot: Bot, state: FSMContext) -> None:
    doc = message.document
    if doc is None:
        return

    # Проверяем что файл — PDF по расширению
    ext = get_extension(doc.file_name, doc.mime_type)
    if ext != ".pdf":
        await message.reply("❌ В режиме склейки принимаю только PDF-файлы.")
        return

    # Проверяем размер
    if doc.file_size and doc.file_size > config.max_file_size_bytes:
        await message.reply(
            f"❌ Файл слишком большой. Максимум: {config.MAX_FILE_SIZE_MB} МБ."
        )
        return

    data = await state.get_data()
    pdf_paths: list[str] = data.get("pdf_paths", [])
    count = len(pdf_paths)

    if count >= MAX_MERGE_FILES:
        await message.reply(
            f"❌ Достигнут максимум: {MAX_MERGE_FILES} файлов. "
            "Нажми «Склеить PDF» для обработки."
        )
        return

    # Скачиваем PDF
    try:
        path = await download_file(bot, doc.file_id, ".pdf")
    except Exception:
        logger.exception("merge: download failed for user %s", message.from_user.id)
        await message.reply("❌ Не удалось скачать файл. Попробуй ещё раз.")
        return

    # Проверяем MIME
    if not validate_file(path, ".pdf"):
        await safe_remove(path)
        await message.reply("❌ Файл не является PDF. Отправь корректный PDF.")
        return

    pdf_paths.append(path)
    await state.update_data(pdf_paths=pdf_paths)

    new_count = len(pdf_paths)
    await message.reply(
        f"✅ PDF {new_count} добавлен. Всего: <b>{new_count} файл(ов)</b>.\n\n"
        "Добавь ещё или нажми «Склеить PDF».",
        reply_markup=get_merge_action_keyboard(),
    )


@router.message(MergeStates.collecting)
async def merge_unknown_message(message: Message) -> None:
    """Обрабатывает нежелательные сообщения во время сбора PDF."""
    await message.reply(
        "📎 Жду PDF-файлы. Отправь документ или нажми «Склеить PDF»."
    )


@router.callback_query(F.data == "merge:done", MergeStates.collecting)
async def handle_merge_done(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    await callback.answer()
    data = await state.get_data()
    pdf_paths: list[str] = data.get("pdf_paths", [])

    if len(pdf_paths) < 2:
        await callback.message.answer(
            "⚠️ Для склейки нужно минимум <b>2 PDF-файла</b>. "
            "Добавь ещё хотя бы один."
        )
        return

    await state.clear()

    # Убираем кнопки у предыдущего сообщения
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    status_msg = await callback.message.answer(
        f"⏳ Склеиваю {len(pdf_paths)} PDF..."
    )
    output_path: Optional[str] = None

    try:
        output_path = await do_merge(pdf_paths)
        result_file = FSInputFile(output_path, filename="merged.pdf")
        await callback.message.answer_document(
            result_file,
            caption=f"✅ Готово — склеено {len(pdf_paths)} файлов — ПДФыч",
        )
    except Exception:
        logger.exception(
            "Merge failed: user=%s, files=%d",
            callback.from_user.id,
            len(pdf_paths),
        )
        await callback.message.answer(
            "❌ Не удалось склеить PDF. Проверь, что все файлы корректные."
        )
    finally:
        await safe_remove_list(pdf_paths)
        await safe_remove(output_path)
        try:
            await status_msg.delete()
        except Exception:
            pass


@router.callback_query(F.data == "merge:cancel", MergeStates.collecting)
async def handle_merge_cancel(
    callback: CallbackQuery, state: FSMContext
) -> None:
    await callback.answer()
    data = await state.get_data()
    pdf_paths: list[str] = data.get("pdf_paths", [])

    await state.clear()

    # Чистим скачанные файлы
    await safe_remove_list(pdf_paths)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await callback.message.answer("❌ Склейка отменена.")
