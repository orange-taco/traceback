FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./

FROM base AS production-dependencies

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM base AS development-dependencies

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-groups --no-install-project

FROM development-dependencies AS development

RUN addgroup --system app && adduser --system --ingroup app app
COPY --chown=app:app . /app

USER app

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM production-dependencies AS production

RUN addgroup --system app && adduser --system --ingroup app app
COPY --chown=app:app . /app

USER app

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=3", "--worker-class=uvicorn_worker.UvicornWorker", "--access-logfile=-", "--error-logfile=-", "config.asgi:application"]
