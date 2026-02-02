# TaskBot Railway Deployment

Это облегчённая версия TaskBot для деплоя на Railway (только API + Frontend).

## Содержит

- **API** (FastAPI) - REST API для управления задачами
- **Frontend** (React + Vite) - веб-интерфейс
- **Database** (SQLite) - локальная база данных

## Что НЕ включает

- Telegram бот (запускается отдельно)
- Голосовые команды (Whisper)
- Планировщик задач (APScheduler)

## Установка локально

```bash
pip install -r requirements.txt
```

## Запуск

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

API доступен на `http://localhost:8000`
Frontend на `http://localhost:8000/`

## Деплой на Railway

1. Создайте репозиторий на GitHub
2. Загрузите код из папки `deploy_railway/`
3. На Railway подключите GitHub репозиторий
4. Railway автоматически найдет `Dockerfile` и развернет

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

## Структура

```
deploy_railway/
├── api/                 # FastAPI приложение
├── database/            # ORM и модели базы
├── webapp_dist/         # Собранный React фронтенд
├── Dockerfile           # Контейнеризация
├── requirements.txt     # Python зависимости
└── .env.example         # Пример переменных окружения
```
