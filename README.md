# Style Assistant Bot

Telegram-бот для подбора образов: онбординг, геолокация/город, событие, стиль, фото (опционально), погодные подсказки и рекомендации.

## Быстрый запуск локально

### 1) Подготовить окружение
```bash
cp .env.example .env
```

Для локального запуска приложения с сервисами в Docker выстави в `.env`:
- `DB_HOST=127.0.0.1`
- `DB_PORT=5444`
- `REDIS_HOST=127.0.0.1`
- `REDIS_PORT=6380`

### 2) Поднять Postgres и Redis
```bash
docker compose -f compose.yml up -d
```

### 3) Установить зависимости Python
```bash
uv sync
```

### 4) Применить миграции
```bash
uv run alembic upgrade head
```

### 5) Запустить бота
```bash
uv run bot-run
```

## `.env`
Ключевые группы переменных:
- `BOT_*` — Telegram и базовые лимиты.
- `GPT_*` — OpenAI.
- `REDIS_*` — FSM storage.
- `DB_*` — Postgres.
- `WEATHER_*`, `MAPS_*` — подготовка под внешние API (пока заглушки в коде).

## Миграции
Миграции упрощены до одной стартовой ревизии:

```bash
uv run alembic upgrade head
```

Это накатит полный текущий schema baseline одной миграцией `c1a2b3d4e5f6`.
