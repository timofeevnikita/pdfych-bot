from __future__ import annotations

import logging

from bot.config import config
from bot.services.image_tools import images_to_pdf, pdf_to_images
from bot.services.libreoffice import convert_with_libreoffice
from bot.services.pdf_tools import merge_pdfs, split_pdf

logger = logging.getLogger(__name__)

# Допустимые пары вход → выход
_OFFICE_EXTS = {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


async def convert(
    input_path: str,
    source_ext: str,
    target_format: str,
) -> str | list[str]:
    """
    Маршрутизирует конвертацию на нужный бэкенд.

    Args:
        input_path:   путь к входному файлу
        source_ext:   расширение источника (напр. '.pdf', '.docx')
        target_format: целевой формат ('pdf', 'docx', 'jpg')

    Returns:
        str  — путь к результирующему файлу  (большинство конвертаций)
        list[str] — список путей (PDF → JPG, постранично)

    Raises:
        ValueError: если пара форматов не поддерживается.
    """
    src = source_ext.lower()
    tgt = target_format.lower()
    tmp = config.TMP_DIR

    if tgt == "pdf":
        if src in _OFFICE_EXTS:
            return await convert_with_libreoffice(input_path, tmp, "pdf")
        if src in _IMAGE_EXTS:
            return await images_to_pdf([input_path], tmp)
        raise ValueError(f"Конвертация {src} → PDF не поддерживается")

    if tgt == "docx":
        if src == ".pdf":
            return await convert_with_libreoffice(input_path, tmp, "docx")
        raise ValueError(f"Конвертация {src} → DOCX не поддерживается")

    if tgt == "jpg":
        if src == ".pdf":
            return await pdf_to_images(input_path, tmp)
        raise ValueError(f"Конвертация {src} → JPG не поддерживается")

    raise ValueError(f"Неизвестный целевой формат: {tgt}")


async def do_merge(pdf_paths: list[str]) -> str:
    """Склеивает несколько PDF в один. Обёртка для удобства из хэндлеров."""
    return await merge_pdfs(pdf_paths, config.TMP_DIR)


async def do_split(pdf_path: str) -> list[str]:
    """Разделяет PDF на страницы. Обёртка для удобства из хэндлеров."""
    return await split_pdf(pdf_path, config.TMP_DIR)
