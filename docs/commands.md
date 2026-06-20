# Development and Production Commands

## Local development

Local development uses:

- `uv` for Python dependencies and Django commands
- locally installed PostgreSQL
- `.env` for local application settings

### Initial setup

Create the PostgreSQL user and database:

```sql
CREATE USER traceback WITH PASSWORD 'development-only';
CREATE DATABASE traceback OWNER traceback;
```

Create the environment and install dependencies:

```sh
cp .env.example .env
uv sync --all-groups
uv run pre-commit install
```

### Run the application

```sh
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py runserver
```

### Django commands

```sh
uv run --env-file .env python manage.py makemigrations
uv run --env-file .env python manage.py migrate
uv run --env-file .env python manage.py createsuperuser
uv run --env-file .env python manage.py shell
```

### Tests and quality checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run yamllint .
uv run python manage.py check --settings=config.settings.test
uv run python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

Run all Git hooks manually:

```sh
uv run pre-commit run --all-files
uv run pre-commit run --all-files --hook-stage pre-push
```

### Dependency management

```sh
uv add <package>
uv add --dev <package>
uv remove <package>
uv lock --upgrade-package <package>
uv lock --upgrade
```

Commit both files after changing dependencies:

```text
pyproject.toml
uv.lock
```

## Production

Production dependencies are installed with `uv sync --frozen` while the Docker
image is built. The running container starts Gunicorn directly; it does not use
`uv run`.

Production `.env` requires at least:

```env
DATABASE_URL=postgresql://...
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=...
```

### Validate the Compose configuration

```sh
APP_IMAGE=traceback-production:local \
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose_prod.yml \
  config
```

### Build a production image locally

```sh
docker build \
  --target production \
  -t traceback-production:local \
  .
```

### Start production containers

```sh
APP_IMAGE=traceback-production:local \
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose_prod.yml \
  up -d --no-build --wait
```

### Production Django commands

```sh
APP_IMAGE=traceback-production:local \
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose_prod.yml \
  run --rm app python manage.py migrate
```

### Status and logs

```sh
APP_IMAGE=traceback-production:local \
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose_prod.yml \
  ps

APP_IMAGE=traceback-production:local \
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose_prod.yml \
  logs -f app
```

### Stop production containers

```sh
APP_IMAGE=traceback-production:local \
docker compose --env-file .env \
  -f docker-compose.yml \
  -f docker-compose_prod.yml \
  down
```

The GitHub deployment workflow builds and pushes the production image, then
runs `docker compose pull app` and `docker compose up -d --no-build --wait app`
on the production EC2 instance.
