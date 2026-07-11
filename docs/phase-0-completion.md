# Phase 0 Completion Criteria

이 문서는 Phase 0 완료 여부를 추적하는 체크리스트다.
Phase 1 Catalog는 이 문서의 필수 항목이 통과하고
`docs/build-plan.md` 완료 이력에 기록된 뒤 시작한다.

## Current Verdict

2026-07-11 기준 Phase 0은 **완료 아님**.

완료된 부분은 Django/DRF scaffold, ASGI entrypoint, `/api/v1/` router,
`/health`, 기본 CI/품질 도구, Docker/Compose 기반이다.

Phase 0 완료를 막는 항목은 custom User/Auth 구현, 공통 API 인프라,
관리자 REST 인증이다. User/Auth 정책 결정은
`docs/phaseB.md`에 확정되어 있으며, 남은 작업은 구현과 검증이다.

## Version Baseline

- Python: `>=3.12,<3.13`
- Django: `>=5.1,<5.3`
- Runtime: Django ASGI application (`config.asgi:application`)
- App server: Gunicorn + Uvicorn worker (`uvicorn_worker.UvicornWorker`)
- API framework: DRF
- Database: PostgreSQL

ASGI 운영을 전제로 하므로 Django는 반드시 `5.1` 이상이어야 한다.
현재 `pyproject.toml`은 `Django>=5.1,<5.3`이고,
현재 lockfile은 `Django 5.2.15`를 설치한다.

## Required Scope

| Area | Completion criteria | Current status |
| --- | --- | --- |
| Project scaffold | Django settings split, ASGI entrypoint, DRF installed, `/api/v1/` router mounted | Done |
| Health check | `GET /health` returns `200 {"status": "ok"}` without auth | Done |
| PostgreSQL | CI migration/test verification uses PostgreSQL; local development documents PostgreSQL migrate path | Done: CI uses PostgreSQL service; local development defaults to Docker Compose PostgreSQL |
| CI | CI runs install, lint, format check, mypy, Django check, migration drift check, migrate, migration check, tests, Compose config, production image build | Workflow includes explicit `migrate --noinput` and `migrate --check`; pending CI run evidence |
| Django version | Dependency range keeps Django `>=5.1,<5.3` for ASGI runtime | Done |
| User | Implement decided custom User before commerce migrations | Decided in `phaseB.md`, missing implementation |
| SocialAccount | Support initial Kakao/Naver social account linking model and constraints | Decided in `phaseB.md`, missing implementation |
| Email/token flows | Email change request and user token baseline for verification/password flows | Decided in `phaseB.md`: email verify 24h, password set/reset 1h, email change 24h with 10m per-user request limit; missing implementation |
| BenefitClaim | Record welcome benefit claims by HMAC phone hash to prevent duplicate issuance | Decided in `phaseB.md`: long-lived HMAC hash ledger without raw personal data; missing implementation |
| SiteSetting | Explicitly defer until Catalog/Order needs concrete public settings or shipping policy | Deferred |
| IdempotencyRecord | Explicitly defer until Order/Payment/admin command APIs introduce idempotent writes | Deferred |
| Error response | DRF exception handler returns stable `code`, `message`, `details`, `request_id` contract | Missing |
| Pagination | Shared DRF pagination class and response contract for list APIs | Missing |
| Request ID | Middleware accepts/generates request ID and exposes it on responses/errors/log context | Missing |
| Admin REST auth | Session authentication + `IsAdminUser` baseline and tests for anonymous/non-staff/staff access | Missing |
| API namespace | Public endpoints live under `/api/v1/`; admin REST endpoints use a clear namespace such as `/api/v1/admin/` | Partial |
| Secrets/settings | Required secrets fail fast outside test; example env documents local values | Partial |
| Tests | Focused tests cover health, request ID, errors, pagination, admin auth, common models, migration health | Partial |
| Docs checkpoint | `docs/build-plan.md` checkpoint and completion history match code and validation evidence | Partial |

## Required Decisions Before Phase 1

1. User/Auth model:
   Implement the custom User/Auth decisions recorded in `docs/phaseB.md`.
2. Admin REST namespace:
   Use `/api/v1/admin/` for the Phase 0B admin REST authentication baseline.
3. SiteSetting:
   Deferred from Phase 0B. Revisit before Phase 1 Catalog if public settings are
   needed for home/PDP, and before Phase 3 Order if shipping fee policy is needed.
4. Idempotency:
   Deferred from Phase 0B. Revisit before Phase 3 Order and Phase 4 Payment because
   command APIs and PG/webhook flows will require idempotency.

## Must Not Include

Phase 0 must not implement commerce domain behavior beyond common foundation:

- Catalog product models or APIs
- Cart/order/payment/inventory business flows
- Seller or marketplace support
- Future admin API endpoints without a current Phase owner

## Missed Items To Resolve Before Phase 1

1. Implement custom User/Auth foundation from `docs/phaseB.md`.
2. Add request/response infrastructure:
   request ID middleware, DRF exception handler, and shared pagination.
3. Add admin REST authentication baseline:
   session authentication with `IsAdminUser` and tests proving anonymous/non-staff
   users are rejected while staff users are accepted.
4. Add tests for the missing common behavior, not only `/health`.
5. Update `docs/build-plan.md` checkpoint and completion history only after the
   above is implemented and verified.

## Phase 0 Completion Command Set

Run these before marking Phase 0 complete:

```bash
uv sync --frozen --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run yamllint .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run pytest
docker compose --env-file .env.example config --quiet
docker compose --env-file .env.example -f docker-compose.yml -f docker-compose_prod.yml config --quiet
docker build --target production .
```

Use `.env` or CI environment variables for commands that require
`DJANGO_SECRET_KEY` and a database URL. Local development may use
`TRACEBACK_DATABASE_URL`; staging/production may use `DATABASE_URL`.
