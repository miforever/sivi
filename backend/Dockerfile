FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ ./src/
COPY static_data/ ./static_data/
COPY manage.py .

RUN uv pip install --system -e .

RUN mkdir -p /app/logs /app/staticfiles

# Collect static files at build time (needed for Django admin UI via WhiteNoise)
ENV DJANGO_SETTINGS_MODULE=config.settings.dev
ENV SECRET_KEY=build-time-placeholder
ENV DEBUG=False
ENV ALLOWED_HOSTS=*
ENV DB_HOST=localhost
ENV DB_NAME=x
ENV DB_USER=x
ENV DB_PASSWORD=x
ENV REDIS_URL=redis://localhost:6379/2
RUN python manage.py collectstatic --noinput

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["python", "-m", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
