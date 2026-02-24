# ПДФыч — Telegram-бот конвертер файлов

Мгновенная конвертация документов и изображений прямо в Telegram.

## Поддерживаемые конвертации

| Вход | Выход |
|------|-------|
| .doc, .docx | .pdf |
| .xls, .xlsx | .pdf |
| .ppt, .pptx | .pdf |
| .jpg, .png, .webp, .heic | .pdf |
| .pdf | .docx |
| .pdf | .jpg (постранично) |
| Несколько .pdf | 1 .pdf (склейка) |
| .pdf | Страницы (разделение) |

## Требования

- Python 3.11+
- LibreOffice (для конвертации офисных форматов)
- Docker + Docker Compose (для деплоя)

## Быстрый старт (Docker)

```bash
# 1. Клонируй репозиторий
git clone <repo-url>
cd glasx-bot

# 2. Создай .env из шаблона
cp .env.example .env

# 3. Вставь токен бота в .env
nano .env   # BOT_TOKEN=...

# 4. Запусти
docker compose up -d

# 5. Логи
docker compose logs -f
```

## Локальный запуск (без Docker)

```bash
# Установи LibreOffice
# Debian/Ubuntu:
sudo apt-get install libreoffice-writer libreoffice-calc libreoffice-impress libmagic1 libheif1

# Создай виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Установи зависимости
pip install -r requirements.txt

# Настрой .env
cp .env.example .env
# Отредактируй .env: добавь BOT_TOKEN

# Запусти
python -m bot.main
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram-бота (обязательно) | — |
| `MAX_FILE_SIZE_MB` | Максимальный размер файла (МБ) | `20` |
| `FREE_DAILY_LIMIT` | Дневной лимит конвертаций | `10` |
| `TMP_DIR` | Директория для временных файлов | `./tmp` |
| `DB_PATH` | Путь к SQLite базе данных | `./data/glasx.db` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `TMP_MAX_AGE_SECONDS` | Время жизни временных файлов (сек) | `300` |

## Архитектура

```
bot/
├── main.py           # Точка входа
├── config.py         # Настройки (pydantic-settings)
├── handlers/         # Обработчики команд и файлов
├── services/         # Бизнес-логика (конвертация)
├── database/         # SQLite: пользователи, история
├── middlewares/      # Throttling, логирование
├── keyboards/        # Inline-клавиатуры
└── utils/            # Вспомогательные функции
```

## Безопасность

- Проверка MIME-типов по magic bytes (не только расширение)
- UUID-имена файлов (защита от path traversal)
- Таймаут LibreOffice 60 сек (защита от зависания)
- Rate limiting: 1 запрос / 3 сек на пользователя
- Глобальный лимит: 10 одновременных обработок
- Docker запускается от непривилегированного пользователя `glasx`
- Параметризованные SQL-запросы (защита от инъекций)
- Автоочистка tmp каждые 60 сек
