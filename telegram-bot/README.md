# Sivi Telegram Bot

Telegram bot interface for the Sivi AI career assistant. Built with aiogram 3 and FastAPI.

## Tech Stack

- **Python 3.12**
- **aiogram 3** — async Telegram bot framework
- **FastAPI** — webhook endpoint and health check
- **uvicorn** — ASGI server
- **Redis** — FSM state and caching
- **httpx / aiohttp** — async HTTP client for backend API calls
- **Pydantic v2** — settings and data validation

## Features

- Resume building via guided conversation
- Job vacancy search and browsing
- Interview practice sessions
- Credit purchases via Click payment
- Multi-language (uz, ru, en)
- Webhook mode (production) and polling mode (development)

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# Fill in: BOT_TOKEN, BACKEND_URL, BACKEND_API_KEY

docker compose up -d
```

### Local development with hot reload

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Exposes Redis on `:6380`, bot on `:8001`, mounts `src/` for hot reload.

### Without Docker

```bash
uv sync
uv run uvicorn src.main:get_app --host 0.0.0.0 --port 8001 --reload
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram bot token from @BotFather |
| `BACKEND_URL` | Yes | Backend API URL (e.g. `http://api:8000/api/`) |
| `BACKEND_API_KEY` | Yes | API key for backend authentication |
| `ADMIN_IDS` | No | JSON array of admin Telegram user IDs |
| `CLICK_TOKEN` | No | Click payment provider token |
| `REDIS_HOST` | No | Redis host (default: `localhost`) |
| `REDIS_PORT` | No | Redis port (default: `6379`) |
| `REDIS_DB` | No | Redis DB number (default: `0`) |
| `DEBUG` | No | Debug mode (default: `False`) |
| `LOG_LEVEL` | No | Log level (default: `INFO`) |
| `WEBHOOK_HOST` | No | Webhook URL for production mode |
| `WEBHOOK_PATH` | No | Webhook path |
| `WEBHOOK_SECRET` | No | Webhook secret token |

## Health Check

```bash
curl http://localhost:8001/health
```

Used by Docker for container health checks (every 30s).

## Nginx

Config for `bot.sivi.uz` lives at `nginx/conf.d/bot.sivi.uz.conf`. Mounted by the deploy nginx container, proxies `/webhook` and `/` to port 8001.

## Project Structure

```
src/
├── main.py           # App factory — FastAPI + aiogram setup
├── config.py         # Pydantic settings
├── api/              # FastAPI routes (health, webhook)
├── handlers/         # Aiogram message and callback handlers
├── keyboards/        # Inline and reply keyboard builders
├── middlewares/      # Aiogram middlewares
├── services/         # Business logic, backend API client
└── utils/            # Helpers and utilities
nginx/
└── conf.d/
    └── bot.sivi.uz.conf    # Nginx config for bot.sivi.uz
```

## Docker Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Base: bot + redis |
| `docker-compose.local.yml` | Local: hot reload, exposed ports |
| `docker-compose.dev.yml` | Dev settings |
| `docker-compose.prod.yml` | Production: resource limits, log levels |

## Code Quality

```bash
ruff check .     # Lint
ruff format .    # Format
pytest           # Tests
```
