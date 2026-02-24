FROM python:3.11-slim

# Устанавливаем системные зависимости:
#   libreoffice-*  — конвертация офисных форматов
#   libmagic1      — определение MIME по magic bytes (python-magic)
#   libheif1       — поддержка HEIC-изображений через Pillow
#   fonts-liberation — базовые шрифты для LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        libreoffice-calc \
        libreoffice-impress \
        libmagic1 \
        libheif1 \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Создаём непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash pdfych

WORKDIR /app

# Устанавливаем Python-зависимости отдельным слоем для кэширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаём директории с правильными правами
RUN mkdir -p tmp data && chown -R pdfych:pdfych /app

# Запускаем от непривилегированного пользователя
USER pdfych

CMD ["python", "-m", "bot.main"]
