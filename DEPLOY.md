# Sivi — VPS Deployment Guide

## Architecture

```
sivi/                          (monorepo)
├── backend/                   Django API + Celery
├── frontend/
│   ├── landing/               Next.js landing (port 3000)
│   └── admin/                 Next.js admin dashboard (port 3001)
├── telegram-bot/              Telegram bot (port 8001)
└── docker/
    ├── docker-compose.yml     Base (all services)
    ├── docker-compose.prod.yml
    ├── nginx/                 All nginx configs
    └── certbot/               SSL certs (gitignored)
```

| Domain | Service |
|--------|---------|
| `sivi.uz` | Landing |
| `admin.sivi.uz` | Admin dashboard |
| `api.sivi.uz` | Backend API |
| `bot.sivi.uz` | Telegram bot webhook |

---

## 1. Server prerequisites

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Point DNS A records to VPS IP: `sivi.uz`, `www.sivi.uz`, `api.sivi.uz`, `admin.sivi.uz`, `bot.sivi.uz`

---

## 2. Clone

```bash
git clone https://github.com/miforever/sivi.git /srv/sivi
```

---

## 3. Environment files

### Backend — `/srv/sivi/backend/.env`

```bash
cp /srv/sivi/backend/env.example /srv/sivi/backend/.env
nano /srv/sivi/backend/.env
```

Key values:
```env
DEBUG=False
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_hex(50))">
ALLOWED_HOSTS=api.sivi.uz
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sivi_db
DB_USER=postgres
DB_PASSWORD=<strong password>
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=sivi_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<same as DB_PASSWORD>
REDIS_URL=redis://redis:6379/2
CORS_ALLOWED_ORIGINS=https://sivi.uz,https://admin.sivi.uz
API_KEYS=<openssl rand -hex 32>
OPENAI_API_KEY=...
FIREWORKS_API_KEY=...
TELETHON_API_ID=...
TELETHON_API_HASH=...
TELETHON_BOT_TOKEN=...
TELETHON_SESSION=...
LOG_LEVEL=WARNING
```

### Telegram bot — `/srv/sivi/telegram-bot/.env`

```env
DEBUG=False
LOG_LEVEL=WARNING
HOST=0.0.0.0
PORT=8001

BOT_TOKEN=<telegram bot token>
ADMIN_IDS=<comma-separated telegram user IDs>
CLICK_TOKEN=<click payment token>

BACKEND_URL=http://api:8000/api/
BACKEND_API_KEY=<same as API_KEYS in backend>

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Webhook — required in production
WEBHOOK_HOST=https://bot.sivi.uz
WEBHOOK_SECRET=<openssl rand -hex 32>
```

---

## 4. Generate Telethon session

The Telegram channel scraper uses Telethon with a StringSession. This is interactive (requires phone number + Telegram code), so run it **locally**, not inside Docker:

```bash
cd backend
# Make sure TELETHON_API_ID and TELETHON_API_HASH are set in .env
# Get these from https://my.telegram.org/apps
uv run python scripts/generate_session.py
```

It will prompt for your phone number and a verification code. Once done, it prints:

```
TELETHON_SESSION=<long string>
```

Copy that value into `/srv/sivi/backend/.env` on the VPS.

---

## 5. SSL certificates

Run before starting nginx (port 80 must be free):

```bash
docker run --rm -p 80:80 \
  -v /srv/sivi/docker/certbot/conf:/etc/letsencrypt \
  -v /srv/sivi/docker/certbot/www:/var/www/certbot \
  certbot/certbot certonly --standalone \
  -d sivi.uz -d www.sivi.uz -d api.sivi.uz -d admin.sivi.uz -d bot.sivi.uz \
  --email your@email.com --agree-tos --no-eff-email
```

---

## 6. Start everything

```bash
cd /srv/sivi/docker
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 7. Post-deploy

```bash
cd /srv/sivi/docker

# Run migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py migrate

# Create admin user
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py create_admin

# Verify
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
curl https://api.sivi.uz/health/
```

---

## Updating

```bash
cd /srv/sivi && git pull

cd docker

# Rebuild specific service
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build api

# Or rebuild everything
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Run migrations if needed
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python manage.py migrate
```

---

## Useful commands

```bash
cd /srv/sivi/docker

# Alias (add to ~/.bashrc):
alias dc='docker compose -f docker-compose.yml -f docker-compose.prod.yml'

# Logs
dc logs -f api
dc logs -f celery
dc logs -f telegram-bot

# Django shell
dc exec api python manage.py shell

# Run scrapers
dc exec api python manage.py scrape_platforms --platform hh_uz
dc exec api python manage.py scrape_platforms --platform olx_uz
dc exec api python manage.py scrape_platforms --platform vacandi_uz

# Database
dc exec db psql -U postgres -d sivi_db

# Renew SSL
dc exec certbot certbot renew
```

---

## Troubleshooting

**pgvector extension missing:**
```bash
dc exec db psql -U postgres -d sivi_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

**Admin 403 Forbidden:**
Ensure `CORS_ALLOWED_ORIGINS` includes `https://admin.sivi.uz` and `API_KEYS` is set.

**Celery not running scheduled tasks:**
Check celery-beat is up: `dc ps celery-beat`
