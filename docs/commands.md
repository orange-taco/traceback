# Development and Production Commands

## Local development

Local development uses:

- Docker Compose for Django and PostgreSQL
- `uv` inside the Docker image to build the Python environment
- `.env` for local application settings

### Initial setup

Create the local environment file:

```sh
cp .env.example .env
```

Start the local stack:

```sh
docker compose --env-file .env up app
```

Local Django runs inside Docker Compose. The app container receives `.env` via
`env_file`, and `TRACEBACK_DATABASE_URL` should point at the Compose PostgreSQL
service name, for example `postgresql://traceback:development-only@db:5432/traceback`.
Compose uses `TRACEBACK_POSTGRES_*` variables for the local database service to
avoid collisions with shell-level `POSTGRES_*` values.

### Run the application

Run the application container against the Compose database:

```sh
docker compose --env-file .env up app
```

Run Django one-off commands inside the app container:

```sh
docker compose --env-file .env run --rm app python manage.py migrate
docker compose --env-file .env run --rm app python manage.py createsuperuser
docker compose --env-file .env run --rm app python manage.py shell
```

### Django commands

```sh
docker compose --env-file .env run --rm app python manage.py makemigrations
docker compose --env-file .env run --rm app python manage.py migrate
docker compose --env-file .env run --rm app python manage.py createsuperuser
docker compose --env-file .env run --rm app python manage.py shell
```

### Tests and quality checks

```sh
docker compose --env-file .env run --rm app pytest
docker compose --env-file .env run --rm app ruff check .
docker compose --env-file .env run --rm app ruff format --check .
docker compose --env-file .env run --rm app mypy .
docker compose --env-file .env run --rm app yamllint .
docker compose --env-file .env run --rm app python manage.py check --settings=config.settings.test
docker compose --env-file .env run --rm app python manage.py makemigrations --check --dry-run --settings=config.settings.test
docker compose --env-file .env run --rm app python manage.py migrate --settings=config.settings.test
docker compose --env-file .env run --rm app python manage.py migrate --check --settings=config.settings.test
```

Run all Git hooks manually:

```sh
docker compose --env-file .env run --rm app pre-commit run --all-files
docker compose --env-file .env run --rm app pre-commit run --all-files --hook-stage pre-push
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
TRACEBACK_DATABASE_URL=postgresql://...
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

### Stop local development containers

```sh
docker compose --env-file .env down
```

The GitHub deployment workflow builds and pushes the production image, then
runs `docker compose pull app` and `docker compose up -d --no-build --wait app`
on the production EC2 instance.
