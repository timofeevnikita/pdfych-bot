from __future__ import annotations

import asyncio
import logging
import os
import uuid
from pathlib import Path
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Семафор ограничивает количество одновременных процессов LibreOffice
_libreoffice_semaphore = asyncio.Semaphore(2)

LIBREOFFICE_TIMEOUT = 120  # секунд (первый запуск на macOS может быть долгим)


async def convert_with_libreoffice(
    input_path: str,
    output_dir: str,
    target_format: str = "pdf",
) -> str:
    """
    Конвертирует файл через LibreOffice CLI (headless).

    Args:
        input_path: путь к входному файлу
        output_dir: директория для сохранения результата
        target_format: целевой формат ('pdf', 'docx')

    Returns:
        Путь к сконвертированному файлу.

    Raises:
        RuntimeError: при ошибке конвертации или таймауте.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Уникальный каталог профиля LibreOffice предотвращает конфликты
    # при параллельном запуске нескольких экземпляров.
    # Профиль в /tmp — абсолютный путь без пробелов/кириллицы для file:// URI
    profile_dir = os.path.join("/tmp", f"lo_profile_{uuid.uuid4().hex}")
    profile_uri = "file://" + quote(str(Path(profile_dir).resolve()))

    async with _libreoffice_semaphore:
        try:
            process = await asyncio.create_subprocess_exec(
                "soffice",
                "--headless",
                "--norestore",
                "--nologo",
                f"-env:UserInstallation={profile_uri}",
                "--convert-to",
                target_format,
                "--outdir",
                output_dir,
                input_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=LIBREOFFICE_TIMEOUT
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.communicate()
                raise RuntimeError(
                    f"LibreOffice превысил лимит ожидания ({LIBREOFFICE_TIMEOUT} сек)"
                )
        finally:
            # Удаляем временный профиль LibreOffice
            _remove_dir(profile_dir)

    if process.returncode != 0:
        err_msg = stderr.decode(errors="replace")[:500]
        logger.error("LibreOffice error (rc=%d): %s", process.returncode, err_msg)
        raise RuntimeError(f"LibreOffice завершился с ошибкой (код {process.returncode})")

    # LibreOffice сохраняет файл с тем же базовым именем, но новым расширением
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.{target_format}")

    if not os.path.isfile(output_path):
        raise RuntimeError(
            f"LibreOffice не создал ожидаемый файл: {output_path}"
        )

    logger.debug(
        "LibreOffice converted %s → %s", input_path, output_path
    )
    return output_path


def _remove_dir(path: str) -> None:
    """Рекурсивно удаляет директорию, игнорируя ошибки."""
    import shutil
    try:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass
