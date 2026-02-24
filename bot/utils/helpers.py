from __future__ import annotations

import os
import re
import uuid
from typing import Optional

import magic


ALLOWED_MIMES: set[str] = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}

# Расширение → ожидаемые MIME-типы
EXT_TO_MIMES: dict[str, set[str]] = {
    ".doc": {"application/msword"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    },
    ".xls": {"application/vnd.ms-excel"},
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    },
    ".ppt": {"application/vnd.ms-powerpoint"},
    ".pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    },
    ".pdf": {"application/pdf"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".heic": {"image/heic", "image/heif"},
}

MIME_TO_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heic",
}


def validate_file(file_path: str, claimed_extension: str) -> bool:
    """Проверяет MIME по содержимому файла (magic bytes), не по расширению."""
    try:
        mime = magic.from_file(file_path, mime=True)
    except Exception:
        return False

    if mime not in ALLOWED_MIMES:
        return False

    allowed_for_ext = EXT_TO_MIMES.get(claimed_extension.lower(), set())
    if allowed_for_ext and mime not in allowed_for_ext:
        return False

    return True


def safe_filename(extension: str) -> str:
    """Генерирует безопасное имя файла на основе UUID. Никогда не использует оригинальное имя."""
    return f"{uuid.uuid4().hex}{extension}"


def sanitize_display_name(name: str) -> str:
    """Безопасное имя для отображения пользователю (убирает path traversal и спецсимволы)."""
    name = os.path.basename(name)  # убиваем ../../../
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name[:200]


def make_output_name(original_name: str, new_extension: str) -> str:
    """Генерирует имя выходного файла для отправки пользователю."""
    base = os.path.splitext(os.path.basename(original_name))[0]
    base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", base)[:100]
    ext = new_extension if new_extension.startswith(".") else f".{new_extension}"
    return f"{base}{ext}"


def get_extension(filename: Optional[str], mime_type: Optional[str]) -> str:
    """Определяет расширение файла по имени или MIME-типу."""
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext:
            return ext
    if mime_type:
        return MIME_TO_EXT.get(mime_type, "")
    return ""


def human_readable_size(size_bytes: int) -> str:
    """Форматирует размер файла в человекочитаемый вид."""
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} КБ"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} МБ"
