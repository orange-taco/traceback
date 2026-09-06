# Phase 0 Completion Criteria

이 문서는 Phase 0 완료 여부를 추적하는 체크리스트다.
Phase 1 Catalog는 이 문서의 필수 항목이 통과하고
`docs/build-plan.md` 완료 이력에 기록된 뒤 시작한다.

## Current Verdict

2026-08-16 기준 Phase 0은 **완료 아님**.

완료된 부분은 Django/DRF scaffold, ASGI entrypoint, 기본 CI/품질 도구,
Docker/Compose 기반, custom User/Auth foundation, 공통 API 인프라,
관리자 REST 인증 baseline, email/password JWT account API다.

Phase 0 완료 전에는 PR #7의 email/password JWT API와 Kakao social login backend,
필요한 frontend account 연동, PostgreSQL 실환경 migrate/test,
production image build 검증을 마무리해야 한다. Phase 1 Catalog는 이 문서의
필수 항목이 통과하고 `docs/build-plan.md` 완료 이력에 기록된 뒤 시작한다.

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
| Project scaffold | Django settings split, ASGI entrypoint, DRF installed, accounts URL mounted | Done |
| PostgreSQL | CI migration/test verification uses PostgreSQL; local development documents PostgreSQL migrate path | Done: CI uses PostgreSQL service; local development defaults to Docker Compose PostgreSQL |
| CI | CI runs install, lint, format check, mypy, Django check, migration drift check, migrate, migration check, tests, Compose config, production image build | Workflow exists; PR #7 Quality/Test/CodeRabbit passed; final Phase 0 CI evidence still pending |
| Django version | Dependency range keeps Django `>=5.1,<5.3` for ASGI runtime | Done |
| User | Implement decided custom User before commerce migrations | Done in Phase 0B |
| SocialAccount | Support initial Kakao/Naver social account linking model and constraints | Model foundation done; Kakao OAuth endpoint flow in PR #7; Naver pending |
| Email/token flows | Email change request and user token baseline for verification/password flows | Model foundation done; email delivery and endpoint flows pending |
| BenefitClaim | Record welcome benefit claims by HMAC phone hash to prevent duplicate issuance | Model foundation done; actual claim issuance flow pending |
| SiteSetting | Explicitly defer until Catalog/Order needs concrete public settings or shipping policy | Deferred |
| IdempotencyRecord | Explicitly defer until Order/Payment/staff command APIs introduce idempotent writes | Deferred |
| Error response | DRF exception handler returns stable `code`, `message`, `details`, `request_id` contract | Done in Phase 0B |
| Pagination | Shared DRF pagination class and response contract for list APIs | Done in Phase 0B |
| Request ID | Middleware accepts/generates request ID and exposes it on responses/errors/log context | Done in Phase 0B |
| Staff API auth | JWT authentication + `IsAdminUser` baseline and tests for anonymous/non-staff/staff access | Implemented as staff permission baseline; Django admin removed |
| API namespace | Account endpoints live under `/api/accounts/`; staff backend namespace is decided by the owning Phase | Current account/auth endpoints done; future staff resources added by owning Phase |
| Secrets/settings | Required secrets fail fast outside test; example env documents local values | Mostly done; final production image/env validation pending |
| Tests | Focused tests cover request ID, errors, pagination, staff auth, account models, serializers, social login service, Kakao provider, migration health | Current local/PR tests passed; PostgreSQL real migrate/test still pending |
| Docs checkpoint | `docs/build-plan.md` checkpoint and completion history match code and validation evidence | Current checkpoint updated; completion history waits for merge/final validation |

## Required Decisions Before Phase 1

1. Kakao social login:
   Implement Kakao first under the existing Kakao/Naver provider decision. Google is
   outside the current Phase 0 provider scope unless separately approved.
2. Client account integration:
   After Kakao backend validation, connect frontend account/social auth flows in
   `../traceback-client`.
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
- Future staff operation API endpoints without a current Phase owner

## Missed Items To Resolve Before Phase 1

1. Complete and merge PR #7 after Kakao backend validation checks.
2. Create or restore `../traceback-client/AGENTS.md` before frontend work, then
   implement client account/social auth integration.
3. Run PostgreSQL real migrate/test and production image build before marking
   Phase 0 complete.
4. Update `docs/build-plan.md` completion history only after the above is
   implemented and verified.

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
`DJANGO_SECRET_KEY` and `TRACEBACK_DATABASE_URL`.
