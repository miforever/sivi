# Sivi Landing Page

Public-facing marketing site for Sivi. Built with Next.js 16, Tailwind CSS 4, and Framer Motion.

## Tech Stack

- **Next.js 16** with React 19 and App Router
- **Tailwind CSS 4** with custom design tokens
- **Framer Motion** for scroll-reveal and page animations
- **TypeScript** strict mode
- **Multi-language** — Uzbek (default), Russian, English via React context

## Sections

| Section | Description |
|---------|-------------|
| Navbar | Floating pill navbar with language switcher |
| Hero | Logo, headline, CTA, stats |
| Features | AI Resume Builder, Job Matching, Interview Prep |
| How It Works | 4-step process |
| Video | Demo video placeholder |
| About | Mission, founder info |
| CTA | Final call-to-action |
| Footer | Links, contact |

## Quick Start

```bash
npm install
npm run dev
# → http://localhost:3000
```

### Docker

```bash
docker build -t sivi-landing .
docker run -p 3000:3000 sivi-landing
```

### Production

Served through `deploy/docker-compose.yml`. The nginx config at `nginx/conf.d/sivi.uz.conf` is mounted by the deploy nginx container and proxies to port 3000.

## Internationalization

Language context lives in `src/i18n/`. Default is **Uzbek**. Users switch via the navbar dropdown.

- `translations.ts` — all strings for `uz`, `ru`, `en`
- `LanguageContext.tsx` — React context + `useLanguage()` hook

## Project Structure

```
src/
├── app/
│   ├── globals.css         # Theme tokens, glass, grid background
│   ├── layout.tsx          # Root layout
│   └── page.tsx            # Entry point with LanguageProvider
├── components/
│   ├── Navbar.tsx          # Animated floating pill + language dropdown
│   ├── Hero.tsx
│   ├── Features.tsx
│   ├── HowItWorks.tsx
│   ├── Video.tsx
│   ├── Pricing.tsx         # Disabled (commented out in page.tsx)
│   ├── About.tsx
│   ├── CTA.tsx
│   ├── Footer.tsx
│   └── ScrollReveal.tsx    # Reusable scroll animation wrapper
└── i18n/
    ├── translations.ts
    └── LanguageContext.tsx
nginx/
└── conf.d/
    └── sivi.uz.conf        # Nginx config for sivi.uz / www.sivi.uz
```

## Scripts

```bash
npm run dev      # Development server
npm run build    # Production build
npm run start    # Start production server
npm run lint     # ESLint
```
