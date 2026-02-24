from __future__ import annotations

import logging
import os
import uuid

import fitz  # PyMuPDF
import img2pdf
from PIL import Image

logger = logging.getLogger(__name__)

# DPI для рендеринга страниц PDF в JPG (zoom = dpi / 72)
PDF_TO_IMAGE_DPI = 150
MAX_PDF_TO_IMAGE_PAGES = 30  # максимум страниц при конвертации PDF → JPG


async def images_to_pdf(image_paths: list[str], output_dir: str) -> str:
    """
    Конвертирует список изображений в один PDF.

    Поддерживает: JPEG, PNG, WEBP, HEIC.
    WEBP и HEIC предварительно конвертируются в PNG через Pillow.

    Returns:
        Путь к созданному PDF.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{uuid.uuid4().hex}.pdf")

    compatible_paths: list[str] = []
    temp_files: list[str] = []

    try:
        for img_path in image_paths:
            ext = os.path.splitext(img_path)[1].lower()
            if ext in {".webp", ".heic"}:
                # Конвертируем через Pillow → PNG для совместимости с img2pdf
                png_path = os.path.join(output_dir, f"{uuid.uuid4().hex}.png")
                with Image.open(img_path) as img:
                    img = img.convert("RGB")
                    img.save(png_path, "PNG")
                compatible_paths.append(png_path)
                temp_files.append(png_path)
            elif ext in {".jpg", ".jpeg"}:
                compatible_paths.append(img_path)
            else:
                # PNG и другие поддерживаемые форматы
                compatible_paths.append(img_path)

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(compatible_paths))

    finally:
        for tmp in temp_files:
            try:
                os.remove(tmp)
            except OSError:
                pass

    logger.debug("images_to_pdf: %d image(s) → %s", len(image_paths), output_path)
    return output_path


async def pdf_to_images(pdf_path: str, output_dir: str) -> list[str]:
    """
    Конвертирует каждую страницу PDF в JPG-файл.

    Returns:
        Список путей к JPG-файлам (в порядке страниц).

    Raises:
        ValueError: если PDF пустой или содержит слишком много страниц.
    """
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = len(doc)

    if total == 0:
        doc.close()
        raise ValueError("PDF не содержит страниц")
    if total > MAX_PDF_TO_IMAGE_PAGES:
        doc.close()
        raise ValueError(
            f"PDF содержит {total} страниц. Максимум для конвертации в JPG: {MAX_PDF_TO_IMAGE_PAGES}"
        )

    zoom = PDF_TO_IMAGE_DPI / 72
    matrix = fitz.Matrix(zoom, zoom)

    output_paths: list[str] = []
    try:
        for i in range(total):
            page = doc[i]
            pix = page.get_pixmap(matrix=matrix)
            out_path = os.path.join(
                output_dir, f"{uuid.uuid4().hex}_p{i + 1:03d}.jpg"
            )
            pix.save(out_path)
            output_paths.append(out_path)
    finally:
        doc.close()

    logger.debug("pdf_to_images: %d page(s) → %s", total, output_dir)
    return output_paths
