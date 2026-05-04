# Sivi Admin Dashboard

Internal admin panel for managing the Sivi platform — users, resumes, vacancies, subscriptions, and analytics.

## Tech Stack

- **Next.js 16** with React 19 and App Router
- **Tailwind CSS 4**
- **Recharts** for analytics charts and dashboards
- **TypeScript** strict mode

## Quick Start

```bash
npm install
npm run dev
# → http://localhost:3001
```

### Docker

```bash
docker build -t sivi-admin .
docker run -p 3001:3001 -e NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 sivi-admin
```

### Production

Served through `deploy/docker-compose.yml`. The nginx config at `nginx/conf.d/admin.sivi.uz.conf` is mounted by the deploy nginx container, proxies `/` to port 3001 and `/api/` to the backend API.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (default: `https://admin.sivi.uz/api/v1`) |

## Project Structure

```
src/
├── app/            # Next.js App Router pages and layouts
├── components/     # UI components (tables, charts, forms)
├── hooks/          # Custom React hooks (data fetching, auth)
└── lib/            # API client, utilities, helpers
nginx/
└── conf.d/
    └── admin.sivi.uz.conf   # Nginx config for admin.sivi.uz
```

## Scripts

```bash
npm run dev      # Development server (port 3001)
npm run build    # Production build
npm run start    # Start production server
npm run lint     # ESLint
```
