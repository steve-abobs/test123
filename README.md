# Document Search Service

Простой сервис полнотекстового поиска по документам.

- Данные документов хранятся в базе данных (PostgreSQL).
- Поисковый индекс (только `id` и `text`) хранится в Elasticsearch.
- API написано на **FastAPI** (async).

## Возможности

- `GET /search?q=...` — полнотекстовый поиск по тексту документа в индексе, возвращает первые
  20 документов **со всеми полями БД** (`id`, `rubrics`, `text`, `created_date`),
  упорядоченные по дате создания (по убыванию).
- `DELETE /documents/{id}` — удаляет документ из БД и из поискового индекса по `id`.
- `GET /health` — проверка живости сервиса.

Спецификация OpenAPI: [`docs.json`](docs.json) (также доступна в рантайме по `/openapi.json`,
а Swagger UI — по `/docs`).

## Структура проекта

```
app/
  config.py          # настройки из переменных окружения
  database.py         # SQLAlchemy async engine/session
  models.py            # ORM-модель Document
  schemas.py            # Pydantic-схемы ответов
  search_backend.py      # абстракция поискового индекса + реализация на Elasticsearch
  dependencies.py          # DI для поискового бэкенда
  services.py                # бизнес-логика поиска и удаления
  routers/                    # HTTP-роуты
  main.py                       # сборка приложения, lifespan (создание таблиц/индекса)
scripts/load_data.py           # загрузка posts.csv в БД и Elasticsearch
tests/                          # функциональные тесты (pytest, httpx, in-memory backend)
docker-compose.yml               # Postgres + Elasticsearch + app + одноразовый loader
```

## Быстрый старт в Docker (рекомендуется)

Требуется Docker и Docker Compose.

```bash
docker compose up --build -d postgres elasticsearch app
```

Дождитесь, пока `elasticsearch` и `postgres` станут healthy (`docker compose ps`), после
чего загрузите тестовые данные из `posts.csv` в БД и индекс:

```bash
docker compose run --rm loader
```

Сервис будет доступен на `http://localhost:8000` (Swagger UI — `http://localhost:8000/docs`).

Примеры запросов:

```bash
curl "http://localhost:8000/search?q=конкурс"
curl -X DELETE "http://localhost:8000/documents/1"
```

Остановить всё:

```bash
docker compose down          # без удаления данных
docker compose down -v       # с удалением volume Postgres
```

## Запуск без Docker (локально)

1. Поднимите PostgreSQL и Elasticsearch самостоятельно, либо только их через Docker:

   ```bash
   docker compose up -d postgres elasticsearch
   ```

2. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Скопируйте `.env.example` в `.env` и при необходимости поправьте значения (по умолчанию
   рассчитаны на `localhost` — совпадают с портами, проброшенными в `docker-compose.yml`):

   ```bash
   cp .env.example .env
   ```

4. Загрузите данные из `posts.csv` (создаёт таблицы и индекс, если их ещё нет):

   ```bash
   python -m scripts.load_data posts.csv
   ```

5. Запустите сервис:

   ```bash
   uvicorn app.main:app --reload
   ```

Сервис будет доступен на `http://localhost:8000`.

## Тесты

Функциональные тесты гоняют реальный HTTP-слой приложения (FastAPI + SQLAlchemy) через
`httpx.AsyncClient`. Чтобы не требовать поднятый Postgres/Elasticsearch для запуска тестов,
БД подменяется на SQLite in-memory, а поисковый индекс — на in-memory реализацию интерфейса
`SearchBackend` (`tests/fakes.py`); сама бизнес-логика и HTTP-роуты при этом не подменяются
и тестируются как есть.

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | хост PostgreSQL |
| `POSTGRES_PORT` | `5432` | порт PostgreSQL |
| `POSTGRES_DB` | `documents` | имя базы данных |
| `POSTGRES_USER` | `documents` | пользователь БД |
| `POSTGRES_PASSWORD` | `documents` | пароль БД |
| `ELASTIC_URL` | `http://localhost:9200` | адрес Elasticsearch |
| `ELASTIC_INDEX` | `documents` | имя индекса |

