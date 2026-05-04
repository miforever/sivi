# Prerequisites

## VPS Requirements

- **OS:** Ubuntu 22.04+ or Debian 12+
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 40GB+ SSD
- **CPU:** 2+ vCPUs

## Software

### Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
docker --version      # 24.0+
docker compose version # v2.20+
```

### Git

```bash
sudo apt install -y git
git --version  # 2.30+
```

## DNS

Point these A records to your VPS IP:

| Record | Domain |
|--------|--------|
| A | `sivi.uz` |
| A | `www.sivi.uz` |
| A | `api.sivi.uz` |
| A | `admin.sivi.uz` |
| A | `bot.sivi.uz` |

## Accounts & API Keys

| Service | Purpose | Where to get |
|---------|---------|--------------|
| **OpenAI** | Resume generation (GPT-4o) | https://platform.openai.com/api-keys |
| **Fireworks AI** | Embeddings for job matching | https://fireworks.ai/account/api-keys |
| **Telegram Bot** | Bot token | https://t.me/BotFather |
| **Telegram API** | Scraping channels (Telethon) | https://my.telegram.org/apps |

## Local Development

### Backend

```bash
# Python 3.12+
python3 --version

# uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

cd backend
uv sync
uv run python manage.py runserver
```

### Frontend (Landing / Admin)

```bash
# Node.js 20+
node --version

cd frontend/landing
npm install
npm run dev        # http://localhost:3000

cd frontend/admin
npm install
npm run dev        # http://localhost:3001
```

### Telegram Bot

```bash
cd telegram-bot
uv sync
uv run python -m src.main
```

### Databases (local)

```bash
# PostgreSQL 16 with pgvector
docker run -d --name sivi-db \
  -e POSTGRES_DB=sivi_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Redis
docker run -d --name sivi-redis -p 6379:6379 redis:7-alpine
```

## Ports

| Port | Service | Environment |
|------|---------|-------------|
| 3000 | Landing | Local dev |
| 3001 | Admin | Local dev |
| 8000 | Backend API | Local dev / Docker |
| 8001 | Telegram bot | Docker |
| 5432 | PostgreSQL | Docker |
| 6379 | Redis | Docker |
| 80 | Nginx (HTTP) | Production |
| 443 | Nginx (HTTPS) | Production |
