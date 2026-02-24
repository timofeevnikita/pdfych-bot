from __future__ import annotations

import logging
import os
import uuid

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

MAX_SPLIT_PAGES = 50  # максимум страниц при разделении


async def merge_pdfs(pdf_paths: list[str], output_dir: str) -> str:
    """
    Склеивает несколько PDF-файлов в один.

    Args:
        pdf_paths: список путей к PDF-файлам (в нужном порядке)
        output_dir: директория для сохранения результата

    Returns:
        Путь к объединённому PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{uuid.uuid4().hex}.pdf")

    writer = PdfWriter()
    for path in pdf_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    logger.debug("Merged %d PDFs → %s", len(pdf_paths), output_path)
    return output_path


async def split_pdf(pdf_path: str, output_dir: str) -> list[str]:
    """
    Разделяет PDF на отдельные страницы.

    Args:
        pdf_path: путь к исходному PDF
        output_dir: директория для сохранения страниц

    Returns:
        Список путей к отдельным страницам (в порядке страниц).

    Raises:
        ValueError: если PDF пустой или слишком большой.
    """
    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(pdf_path)
    total = len(reader.pages)

    if total == 0:
        raise ValueError("PDF не содержит страниц")
    if total > MAX_SPLIT_PAGES:
        raise ValueError(
            f"PDF содержит {total} страниц. Максимум для разделения: {MAX_SPLIT_PAGES}"
        )

    output_paths: list[str] = []
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = os.path.join(output_dir, f"{uuid.uuid4().hex}_p{i + 1:03d}.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)
        output_paths.append(out_path)

    logger.debug("Split PDF into %d pages → %s", total, output_dir)
    return output_paths


def get_pdf_page_count(pdf_path: str) -> int:
    """Возвращает количество страниц в PDF."""
    reader = PdfReader(pdf_path)
    return len(reader.pages)
