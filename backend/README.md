# Sivi Backend

Django REST API powering the Sivi career assistant. Handles resumes, vacancy scraping, semantic job matching, subscriptions, credits, and interview questions.

## Tech Stack

- **Python 3.12** with **Django 4.2 LTS** and **Django REST Framework**
- **PostgreSQL 16** with **pgvector** extension for vector similarity search
- **Redis** — Celery broker and cache
- **Celery** — Background task processing (embedding generation)
- **Fireworks AI** — BGE-M3 embeddings (1024 dimensions) for semantic matching
- **OpenAI** — Resume data extraction and generation
- **uv** — Package management

## Features

- **Resume CRUD** — Upload, create from Q&A, enhance with AI, export as PDF (en/ru/uz)
- **Vacancy Scraping** — Telegram channels (17 parsers, Telethon) + job platforms (hh.uz, it-market.uz, olx.uz, vacandi.uz, gorodrabot.uz, ishkop.uz, uzairways)
- **Semantic Matching** — pgvector HNSW index matches resumes to vacancies via cosine similarity
- **Subscriptions** — Monthly/quarterly plans with Click payment integration
- **Credit System** — Pay-per-use credits for AI operations (extraction, generation, enhancement)
- **Interview Questions** — Question catalog filtered by position and language
- **Referrals & Promo Codes** — User growth and discount systems

## Quick Start

### Docker (recommended)

```bash
cp .env.example .env
# Fill in: SECRET_KEY, DB credentials, OPENAI_API_KEY, API_KEYS

docker compose up -d
docker compose exec api python manage.py migrate
docker compose exec api python manage.py import_subscription_plans
docker compose exec api python manage.py import_packages
docker compose exec api python manage.py import_questions
```

Services on the `sivi` network:
- `api` — Django dev server (port 8000)
- `db` — PostgreSQL 16 with pgvector
- `redis` — Broker and cache
- `celery` — Background worker

### Local development

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## Apps

| App | Purpose |
|---|---|
| `users` | User model with Telegram ID, credits balance |
| `resumes` | Resume CRUD, AI extraction/generation, PDF export |
| `vacancies` | Vacancy model, scrapers (channels + platforms) |
| `matching` | pgvector semantic search, embedding services |
| `subscriptions` | Subscription plans, activation, status |
| `store` | Credit packages, purchase transactions |
| `questions` | Interview question catalog |
| `referrals` | Referral tracking |
| `promocodes` | Promo code system |
| `common` | Auth classes, permissions, response helpers |

## Celery Schedules

- **Telegram Channels**: Every 4 hours (top of the hour)
- **Fast Job Platforms** (hh.uz, olx.uz, vacandi.uz, gorodrabot.uz, ishkop.uz): Every 2 hours
- **Daily Platforms** (it-market.uz, uzairways): Once a day
- **Embeddings Backfill**: Every 2 hours (offset by 15 mins)
- **Stale Vacancy Purge**: Daily at 4:00 AM

## Management Commands

```bash
# Scrape vacancies
python manage.py scrape_channels              # All Telegram channels
python manage.py scrape_channels --channel=channel_name
python manage.py scrape_platforms             # All platforms (hh.uz, it-market.uz, olx.uz, vacandi.uz, gorodrabot.uz, ishkop.uz, uzairways)
python manage.py scrape_platforms --platform=hh_uz

# Generate embeddings
python manage.py backfill_embeddings          # All vacancies missing embeddings
python manage.py backfill_embeddings --batch-size=64

# Seed data
python manage.py import_subscription_plans
python manage.py import_packages
python manage.py import_questions
```

## Authentication

Two authentication methods:

1. **Telegram Bot Auth** — `X-API-KEY` + `X-Telegram-Id` headers (resolves to User)
2. **JWT** — `Authorization: Bearer <token>` header

## API Endpoints

### Users
- `POST /api/v1/user/telegram/` — Register user
- `GET /api/v1/user/telegram/me/` — Get current user

### Resumes
- `GET /api/v1/resumes/` — List resumes
- `POST /api/v1/resumes/` — Create resume with nested sections
- `GET /api/v1/resumes/{id}/` — Resume detail
- `PUT|PATCH /api/v1/resumes/{id}/` — Update resume
- `DELETE /api/v1/resumes/{id}/` — Delete resume
- `POST /api/v1/resumes/extract/` — Extract data from PDF/DOCX (free)
- `POST /api/v1/resumes/generate-from-qa/` — Generate from Q&A (1 credit)
- `POST /api/v1/resumes/{id}/enhance/` — AI enhancement (1 credit)
- `POST /api/v1/resumes/generate-pdf/` — Preview PDF from JSON
- `GET /api/v1/resumes/{id}/export-pdf/` — Download saved resume as PDF

### Matching
- `POST /api/v1/matching/find-jobs/` — Semantic job search for a resume

### Subscriptions
- `GET /api/v1/subscriptions/plans/` — Available plans
- `GET /api/v1/subscriptions/status/` — User subscription status
- `POST /api/v1/subscriptions/activate/` — Activate subscription
- `POST /api/v1/subscriptions/renew/` — Renew subscription

### Credits
- `GET /api/v1/resumes/credits/` — Credit balance
- `GET /api/v1/resumes/credit-packages/` — Available packages
- `POST /api/v1/resumes/purchase-credits/` — Purchase credits

### Vacancies
- `GET /api/v1/vacancies/` — List vacancies
- `GET /api/v1/vacancies/{id}/` — Vacancy detail

### Questions
- `GET /api/v1/questions/` — List questions (filter by `lang`, `position`)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key |
| `API_KEYS` | Yes | Comma-separated valid API keys |
| `OPENAI_API_KEY` | Yes | OpenAI API key for resume AI |
| `FIREWORKS_API_KEY` | Yes | Fireworks AI key for embeddings |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Yes | PostgreSQL credentials |
| `REDIS_URL` | No | Redis URL (default: `redis://redis:6379/0`) |
| `SENTRY_DSN` | No | Sentry error tracking |
| `USE_S3` | No | Enable S3 file storage |

## Project Structure

```
src/
├── apps/
│   ├── common/         # Auth, permissions, responses, exceptions
│   ├── matching/       # Embedding services, pgvector matching, Celery tasks
│   ├── promocodes/     # Promo code system
│   ├── questions/      # Interview question catalog
│   ├── referrals/      # Referral tracking
│   ├── resumes/        # Resume CRUD, AI services, PDF generation
│   ├── store/          # Credit packages, transactions
│   ├── subscriptions/  # Plans, activation, status
│   ├── users/          # User model, Telegram registration
│   └── vacancies/      # Vacancy model, scrapers (channels + platforms)
└── config/
    ├── settings/       # Django settings (base, dev, prod)
    ├── urls.py
    ├── celery.py
    └── wsgi.py
```

## Code Quality

```bash
ruff check .    # Lint
ruff format .   # Format
pytest          # Tests
```
