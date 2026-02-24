from __future__ import annotations

import asyncio
import logging
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import config
from bot.database.db import check_daily_limit, log_conversion
from bot.keyboards.inline import get_pdf_format_keyboard
from bot.services.converter import convert
from bot.services.file_manager import download_file, safe_remove, safe_remove_list
from bot.utils.helpers import (
    get_extension,
    human_readable_size,
    make_output_name,
    sanitize_display_name,
    validate_file,
)

logger = logging.getLogger(__name__)

router = Router()

# Небольшая задержка между отправкой страниц, чтобы не получить flood-wait
_PAGE_SEND_DELAY = 0.15  # секунд


class ConvertStates(StatesGroup):
    waiting_format = State()  # ждём выбор формата для PDF-файла


@router.message(F.document)
async def handle_document(message: Message, bot: Bot, state: FSMContext) -> None:
    doc = message.document
    if doc is None:
        return

    # 1. Валидация размера ДО скачивания
    if doc.file_size and doc.file_size > config.max_file_size_bytes:
        await message.reply(
            f"❌ Файл слишком большой. Максимум: <b>{config.MAX_FILE_SIZE_MB} МБ</b>"
        )
        return

    # 2. Определяем расширение по имени файла / MIME
    ext = get_extension(doc.file_name, doc.mime_type)
    if not ext or ext not in config.allowed_extensions_set:
        await message.reply(
            "❌ Формат не поддерживается.\n\n"
            "Принимаю: Word, Excel, PowerPoint, PDF, JPG, PNG, WEBP, HEIC."
        )
        return

    # 3. Проверка дневного лимита
    if not await check_daily_limit(message.from_user.id, config.FREE_DAILY_LIMIT):
        await message.reply(
            f"⚠️ Ты исчерпал дневной лимит: <b>{config.FREE_DAILY_LIMIT} файлов</b>. "
            "Попробуй завтра."
        )
        return

    # 4. Если PDF — предлагаем выбрать формат через кнопки
    if ext == ".pdf":
        display_name = sanitize_display_name(doc.file_name or "document.pdf")
        size_str = human_readable_size(doc.file_size or 0)

        await state.update_data(
            file_id=doc.file_id,
            file_name=doc.file_name or "document.pdf",
            file_size=doc.file_size,
            source_ext=ext,
        )
        await state.set_state(ConvertStates.waiting_format)

        await message.reply(
            f"Файл: <b>{display_name}</b> ({size_str})\n\nКонвертировать в:",
            reply_markup=get_pdf_format_keyboard(),
        )
        return

    # 5. Для остальных форматов — конвертируем сразу в PDF
    await _run_conversion(
        message=message,
        bot=bot,
        file_id=doc.file_id,
        file_name=doc.file_name or f"file{ext}",
        file_size=doc.file_size,
        source_ext=ext,
        target_format="pdf",
    )


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    """Обработка фото, отправленных как сжатые изображения (не документ)."""
    # Берём самое большое разрешение (последний элемент)
    photo = message.photo[-1]

    # Проверка дневного лимита
    if not await check_daily_limit(message.from_user.id, config.FREE_DAILY_LIMIT):
        await message.reply(
            f"⚠️ Ты исчерпал дневной лимит: <b>{config.FREE_DAILY_LIMIT} файлов</b>. "
            "Попробуй завтра."
        )
        return

    await _run_conversion(
        message=message,
        bot=bot,
        file_id=photo.file_id,
        file_name="photo.jpg",
        file_size=photo.file_size,
        source_ext=".jpg",
        target_format="pdf",
    )


@router.callback_query(F.data.startswith("convert:"), ConvertStates.waiting_format)
async def handle_format_selection(
    callback: CallbackQuery, bot: Bot, state: FSMContext
) -> None:
    await callback.answer()

    target_format = callback.data.split(":")[1]  # "docx" или "jpg"
    data = await state.get_data()
    await state.clear()

    file_id: str = data["file_id"]
    file_name: str = data["file_name"]
    file_size: Optional[int] = data.get("file_size")
    source_ext: str = data["source_ext"]

    # Редактируем сообщение с кнопками — убираем клавиатуру
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await _run_conversion(
        message=callback.message,
        bot=bot,
        file_id=file_id,
        file_name=file_name,
        file_size=file_size,
        source_ext=source_ext,
        target_format=target_format,
    )


async def _run_conversion(
    *,
    message: Message,
    bot: Bot,
    file_id: str,
    file_name: str,
    file_size: Optional[int],
    source_ext: str,
    target_format: str,
) -> None:
    """Скачивает файл, конвертирует и отправляет результат пользователю."""

    status_msg = await message.answer("⏳ Конвертирую...")

    input_path: Optional[str] = None
    output_paths: list[str] = []

    try:
        # Скачиваем файл
        input_path = await download_file(bot, file_id, source_ext)

        # Проверяем MIME по содержимому (magic bytes)
        if not validate_file(input_path, source_ext):
            await message.answer(
                "❌ Содержимое файла не соответствует расширению. "
                "Проверь файл и попробуй снова."
            )
            return

        # Конвертируем
        result = await convert(input_path, source_ext, target_format)

        # result: str или list[str]
        if isinstance(result, list):
            output_paths = result
        else:
            output_paths = [result]

        user_id = message.from_user.id if message.from_user else 0

        # Отправляем результат(ы)
        if len(output_paths) == 1:
            out_name = make_output_name(file_name, target_format)
            result_file = FSInputFile(output_paths[0], filename=out_name)
            await message.answer_document(result_file, caption="✅ Готово — ПДФыч")
        else:
            # Несколько файлов (PDF → JPG, постранично)
            total = len(output_paths)
            for i, path in enumerate(output_paths):
                page_num = i + 1
                fname = f"page_{page_num:03d}.jpg"
                result_file = FSInputFile(path, filename=fname)
                caption = f"✅ Готово — ПДФыч" if page_num == total else None
                await message.answer_document(result_file, caption=caption)
                if i < total - 1:
                    await asyncio.sleep(_PAGE_SEND_DELAY)

        # Логируем успех
        await log_conversion(
            user_id=user_id,
            input_format=source_ext,
            output_format=f".{target_format}",
            file_size=file_size,
            success=True,
        )

    except ValueError as e:
        logger.warning("Conversion ValueError user=%s: %s", message.from_user.id if message.from_user else "?", e)
        await message.answer(f"❌ {e}")
        await log_conversion(
            user_id=message.from_user.id if message.from_user else 0,
            input_format=source_ext,
            output_format=f".{target_format}",
            file_size=file_size,
            success=False,
        )
    except Exception:
        logger.exception(
            "Conversion failed: user=%s file=%s → %s",
            message.from_user.id if message.from_user else "?",
            source_ext,
            target_format,
        )
        await message.answer(
            "❌ Не удалось конвертировать файл. Попробуй другой файл или формат."
        )
        await log_conversion(
            user_id=message.from_user.id if message.from_user else 0,
            input_format=source_ext,
            output_format=f".{target_format}",
            file_size=file_size,
            success=False,
        )
    finally:
        await safe_remove(input_path)
        await safe_remove_list(output_paths)
        try:
            await status_msg.delete()
        except Exception:
            pass
