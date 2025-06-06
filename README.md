# LLMTenderBot

Telegram-бот для анализа тендерной документации с использованием больших языковых моделей (LLM). Бот может обрабатывать документы, извлекать ключевую информацию и предоставлять структурированный анализ тендеров.

## Возможности

- 📄 Анализ тендерных документов различных форматов
- 🤖 Интеграция с локальными LLM через Ollama
- 🔗 Поддержка Mistral API для OCR и анализа
- 📱 Простой интерфейс через Telegram
- 🔍 Семантическое разделение документов
- 📊 Структурированный вывод результатов анализа

## Требования

- Python 3.11+
- Docker и Docker Compose (для контейнерной установки)
- Токен Telegram бота
- Доступ к Ollama или Mistral API

## Установка

### Способ 1: Используя Docker (Рекомендуется)

1. **Клонирование репозитория:**
   ```bash
   git clone https://github.com/SavinMA/LLMTenderBot.git
   cd LLMTenderBot
   ```

2. **Настройка переменных окружения:**
   ```bash
   # Скопируйте файл примера
   cp example.env .env
   
   # Отредактируйте .env файл своими значениями
   nano .env
   ```
   
   Заполните следующие переменные:
   ```env
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   
   # Analyzer Configuration
   ANALYZER_TYPE=mistral  # или ollama
   
   # LLM Configuration (для Ollama)
   LLM_MODEL=llama3.2:3b  # модель для Ollama
   LLM_HOST=http://ollama:11434  # хост Ollama в Docker
   
   # Mistral Configuration (для Mistral API)
   MISTRAL_API_KEY=your_mistral_api_key_here
   MISTRAL_MODEL=mistral-small-latest  # модель Mistral
   ```

3. **Запуск с Docker Compose:**
   ```bash
   # Сборка и запуск всех сервисов
   docker-compose up --build -d
   
   # Проверка статуса контейнеров
   docker-compose ps
   
   # Просмотр логов
   docker-compose logs -f llmtenderbot
   ```

4. **Настройка Ollama модели:**
   ```bash
   # Подключение к контейнеру Ollama
   docker exec -it ollama ollama pull llama3.2:3b
   
   # Или установка другой модели
   docker exec -it ollama ollama pull mistral:7b
   ```

### Способ 2: Локальная установка

1. **Клонирование репозитория:**
   ```bash
   git clone https://github.com/SavinMA/LLMTenderBot.git
   cd LLMTenderBot
   ```

2. **Создание виртуального окружения:**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Установка зависимостей:**
   ```bash
   # Основные зависимости
   pip install -r requirements.txt
   
   # Установка пакета в режиме разработки
   pip install -e .
   
   # Для разработчиков (опционально)
   pip install -e .[dev]
   ```

4. **Настройка переменных окружения:**
   ```bash
   cp example.env .env
   # Отредактируйте .env файл
   ```

5. **Установка и настройка Ollama (если используете локально):**
   ```bash
   # Установите Ollama с официального сайта
   # https://ollama.ai/
   
   # Запустите Ollama
   ollama serve
   
   # В другом терминале установите модель
   ollama pull llama3.2:3b
   ```

6. **Запуск бота:**
   ```bash
   python src/main.py
   ```

## Использование

1. **Запуск бота:** Отправьте команду `/start` вашему боту в Telegram
2. **Отправка документа:** Загрузите документ для анализа
3. **Получение результата:** Бот обработает документ и вернет структурированный анализ

## Структура проекта

```
LLMTenderBot/
├── src/                           # Исходный код
│   ├── __init__.py               # Инициализация пакета
│   ├── main.py                   # Точка входа приложения
│   ├── telegram_bot.py           # Telegram бот логика
│   ├── config.py                 # Конфигурация приложения
│   ├── mistral_analyzer.py       # Анализатор на Mistral API
│   ├── local_LLM_analyzer.py     # Локальный LLM анализатор (Ollama)
│   ├── documents_analyzer.py     # Базовый класс анализатора
│   ├── prompts.py                # Промпты для LLM
│   ├── queries.py                # Модели данных Pydantic
│   ├── ocr/                      # Модуль распознавания текста
│   │   └── mistral_ocr.py        # OCR через Mistral API
│   └── splitters/                # Модули для разделения текста
│       └── semantic_splitter.py  # Семантическое разделение документов
├── data/                         # Директория для данных
├── logs/                         # Директория для логов
├── venv/                         # Виртуальное окружение Python
├── .vscode/                      # Настройки VS Code
├── .git/                         # Git репозиторий
├── requirements.txt              # Python зависимости
├── setup.py                      # Установочный скрипт
├── Dockerfile                    # Docker образ
├── docker-compose.yml            # Docker Compose для разработки
├── docker-compose.prod.yml       # Docker Compose для продакшена
├── .dockerignore                 # Исключения для Docker
├── .gitignore                    # Исключения для Git
├── example.env                   # Пример переменных окружения
├── deploy.sh                     # Скрипт развертывания (Linux/macOS)
├── deploy.ps1                    # Скрипт развертывания (Windows)
├── Makefile                      # Makefile для автоматизации задач
├── LICENSE                       # Лицензия MIT
└── README.md                     # Документация проекта
```

## Управление и развертывание

### Автоматическое развертывание

Проект включает скрипты для автоматизации развертывания:

**Windows (PowerShell):**
```powershell
# Развертывание в режиме разработки
.\deploy.ps1

# Развертывание в продакшене
.\deploy.ps1 -Production
```

**Linux/macOS (Bash):**
```bash
# Развертывание в режиме разработки
./deploy.sh

# Развертывание в продакшене
./deploy.sh prod
```

### Использование Makefile

```bash
# Установка зависимостей
make install

# Запуск в режиме разработки
make dev

# Запуск в продакшене
make prod

# Просмотр логов
make logs

# Остановка сервисов
make stop

# Полная очистка
make clean
```

### Ручное управление Docker

```bash
# Запуск сервисов (разработка)
docker-compose up -d

# Запуск сервисов (продакшен)
docker-compose -f docker-compose.prod.yml up -d

# Остановка сервисов
docker-compose down

# Просмотр логов
docker-compose logs -f llmtenderbot

# Обновление образов
docker-compose pull && docker-compose up -d

# Полная очистка
docker-compose down -v --rmi all
```

## Переменные окружения

| Переменная | Описание | Обязательная | Значение по умолчанию |
|------------|----------|--------------|----------------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | Да | - |
| `ANALYZER_TYPE` | Тип анализатора (`mistral` или `ollama`) | Да | `mistral` |
| `LLM_MODEL` | Название модели для Ollama | Да (для Ollama) | - |
| `LLM_HOST` | URL хоста Ollama | Да (для Ollama) | - |
| `MISTRAL_API_KEY` | API ключ Mistral | Да (для Mistral) | - |
| `MISTRAL_MODEL` | Модель Mistral для анализа | Да (для Mistral) | - |

### Настройка анализаторов

**Для использования Mistral API:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ANALYZER_TYPE=mistral
MISTRAL_API_KEY=your_mistral_api_key_here
MISTRAL_MODEL=mistral-small-latest
```

**Для использования локального Ollama:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ANALYZER_TYPE=ollama
LLM_MODEL=llama3.2:3b
LLM_HOST=http://localhost:11434
```

**Для Docker окружения с Ollama:**
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ANALYZER_TYPE=ollama
LLM_MODEL=llama3.2:3b
LLM_HOST=http://ollama:11434
```

## Разработка

Для разработки рекомендуется использовать:

```bash
# Установка зависимостей для разработки
pip install -e .[dev]

# Форматирование кода
black src/

# Проверка кода
flake8 src/

# Запуск тестов
pytest
```

## Устранение неисправностей

### Проблемы с Docker

```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов конкретного сервиса
docker-compose logs ollama
docker-compose logs llmtenderbot

# Перезапуск сервиса
docker-compose restart llmtenderbot
```

### Проблемы с Ollama

```bash
# Проверка доступных моделей
docker exec -it ollama ollama list

# Загрузка модели заново
docker exec -it ollama ollama pull llama3.2:3b

# Проверка подключения
curl http://localhost:11434/api/tags
```

## Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## Контакты

- GitHub: [SavinMA](https://github.com/SavinMA)
- Email: ctok81@gmail.com 