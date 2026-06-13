FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY . /app

RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi \
    && chown -R app:app /app

USER app

FROM base AS development

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS production

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
