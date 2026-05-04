# Sivi

AI-powered career assistant for the Uzbekistan job market. Helps users build resumes, find matching vacancies, and prepare for interviews — delivered via Telegram bot.

## What it does

- **Resume builder** — create, enhance with AI, and export as PDF (en/ru/uz)
- **Semantic job matching** — pgvector cosine similarity matches your resume to relevant vacancies
- **Vacancy aggregation** — scrapes 10 job platforms and 17 Telegram channels every few hours
- **Subscriptions & credits** — monthly/quarterly plans + pay-per-use AI credits (Click payment)
- **Interview prep** — question catalog filtered by position and language

## Architecture

```
sivi/
├── backend/          Django REST API + Celery workers
├── frontend/
│   ├── landing/      Next.js public site  (sivi.uz)
│   └── admin/        Next.js admin panel  (admin.sivi.uz)
├── telegram-bot/     aiogram Telegram bot (bot.sivi.uz)
└── docker/           Docker Compose + Nginx configs
```

| Domain | Service |
|---|---|
| `sivi.uz` | Landing |
| `admin.sivi.uz` | Admin dashboard |
| `api.sivi.uz` | Backend API |
| `bot.sivi.uz` | Telegram bot webhook |

## Tech stack

| Layer | Technologies |
|---|---|
| Backend | Python 3.12, Django 4.2 LTS, Django REST Framework |
| Database | PostgreSQL 16 + pgvector (HNSW index, cosine similarity) |
| Queue | Redis + Celery |
| AI | OpenAI (GPT-4o) · Fireworks AI (BGE-M3 embeddings, 1024-dim) |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Bot | aiogram |
| Infra | Docker Compose, Nginx, Let's Encrypt |

## Vacancy sources

### Job platforms (10)

| Platform | URL | Scrape frequency |
|---|---|---|
| hh.uz | https://hh.uz | Every 2 hours |
| OLX.uz | https://www.olx.uz | Every 2 hours |
| Vacandi.uz | https://vacandi.uz | Every 2 hours |
| Ishkop.uz | https://ishkop.uz | Every 2 hours |
| Ish.uz | https://ish.uz | Every 2 hours |
| IshPlus.uz | https://ishplus.uz | Every 2 hours |
| OsonIsh.uz | https://osonish.uz | Every 2 hours |
| Argos.uz | https://vacancy.argos.uz | Every 2 hours |
| it-market.uz | https://it-market.uz | Daily |
| Uzbekistan Airways | https://corp.uzairways.com | Daily |

### Telegram channels (17)

| Channel | Handle | Focus |
|---|---|---|
| Click Jobs | @click_jobs | General |
| Tashkent Jobs | @clozjobs | General |
| DATA \| ISH | @data_ish | Data / Analytics |
| Doda Jobs | @doda_jobs | General |
| Edu Vakansiya | @edu_vakansiya | Education |
| Example.uz - IT Jobs | @Exampleuz | IT |
| HR job Uzbekistan | @hrjobuz | HR |
| Ishmi-ish | @ishmi_ish | IT & General |
| Uzbekistan IT Jobs | @ITjobs_Uzbekistan | IT |
| IT Park Uzbekistan | @itpark_uz | IT |
| LinkedIn Jobs Uzbekistan | @linkedinjobsuzbekistan | General |
| Python Jobs | @python_djangojobs | Python / Django |
| Ustoz-Shogird | @UstozShogird | Education / Mentorship |
| TashJob - Uzbekistan ishbor | @uzbekistanishborwork | General |
| UzDev Jobs | @uzdev_jobs | IT |
| UzJobs.uz | @UzjobsUz | General |
| Vacancy Uzbekistan Airports | @vacancyuzairports | Aviation |

## Getting started

See [PREREQUISITES.md](PREREQUISITES.md) for local dev setup and [DEPLOY.md](DEPLOY.md) for VPS deployment.

**Quick local start:**

```bash
# Backend
cd backend && cp .env.example .env   # fill in required keys
docker compose up -d
docker compose exec api python manage.py migrate

# Landing
cd frontend/landing && npm install && npm run dev   # http://localhost:3000

# Admin
cd frontend/admin  && npm install && npm run dev   # http://localhost:3001

# Telegram bot
cd telegram-bot && uv sync && uv run python -m src.main
```

## Repo structure

| Directory | README |
|---|---|
| `backend/` | [backend/README.md](backend/README.md) |
| `frontend/landing/` | [frontend/landing/README.md](frontend/landing/README.md) |
| `frontend/admin/` | [frontend/admin/README.md](frontend/admin/README.md) |
| `telegram-bot/` | [telegram-bot/README.md](telegram-bot/README.md) |
