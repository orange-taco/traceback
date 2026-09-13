# Phase 0 Completion Criteria

이 문서는 Phase 0 완료 여부를 추적하는 체크리스트다.
Phase 1 Catalog는 이 문서의 필수 항목이 통과하고
`docs/build-plan.md` 완료 이력에 기록된 뒤 시작한다.

## Current Verdict

2026-09-13 기준 Phase 0은 **완료 아님**.

완료된 부분은 Django/DRF scaffold, ASGI entrypoint, 기본 CI/품질 도구,
Docker/Compose 기반, custom User/Auth foundation, 공통 API 인프라,
관리자 REST 인증 baseline과 allauth Headless account auth다.

Phase 0 완료 전에는 실제 교차 로그인과 DB 중복 검증, frontend account QA,
production image/reverse proxy/SMTP 검증을 마쳐야 한다. Phase 1 Catalog는
필수 항목이 통과하고 `docs/build-plan.md` 완료 이력에 기록된 뒤 시작한다.

## Server-first scope decision (2026-09-13)

The user requested server completion first. Client password-change UI and MCP
UI acceptance are deferred, with actionable handoff in `current/README.md`.
Server implementation, PostgreSQL/session contract verification, and scoped QA
cleanup pass. This scope split does not mark all of Phase 0 done.

## Version Baseline

- Python: `>=3.14,<3.15`
- Django: `>=6.1,<6.2`
- Runtime: Django ASGI application (`config.asgi:application`)
- App server: Gunicorn + Uvicorn worker (`uvicorn_worker.UvicornWorker`)
- API framework: DRF
- Database: PostgreSQL

현재 lockfile은 Python 3.14와 Django 6.1.1을 기준으로 검증한다.

## Required Scope

| Area | Completion criteria | Current status |
| --- | --- | --- |
| Project scaffold | Django settings split, ASGI entrypoint, DRF installed, accounts URL mounted | Done |
| PostgreSQL | CI migration/test verification uses PostgreSQL; local development documents PostgreSQL migrate path | Done: CI uses PostgreSQL service; local development defaults to Docker Compose PostgreSQL |
| CI | CI runs install, lint, format check, mypy, Django check, migration drift check, migrate, migration check, tests, Compose config, production image build | Workflow exists; PR #7 Quality/Test/CodeRabbit passed; final Phase 0 CI evidence still pending |
| Django version | Dependency range keeps Django `>=6.1,<6.2` on Python 3.14 | Done |
| User | Implement decided custom User before commerce migrations | Done in Phase 0B |
| Account auth | allauth Headless email verification, password login/reset, logout, DB session | Implemented and locally tested |
| SocialAccount | allauth Kakao login and verified-email account connection | Basic real login observed; PostgreSQL mocked-provider cross-route tests and QA cleanup passed; real cross-route browser QA pending |
| BenefitClaim | Record welcome benefit claims by HMAC phone hash to prevent duplicate issuance | Model foundation done; actual claim issuance flow pending |
| SiteSetting | Explicitly defer until Catalog/Order needs concrete public settings or shipping policy | Deferred |
| IdempotencyRecord | Explicitly defer until Order/Payment/staff command APIs introduce idempotent writes | Deferred |
| Error response | DRF exception handler returns stable `code`, `message`, `details`, `request_id` contract | Done in Phase 0B |
| Pagination | Shared DRF pagination class and response contract for list APIs | Done in Phase 0B |
| Request ID | Middleware accepts/generates request ID and exposes it on responses/errors/log context | Done in Phase 0B |
| Staff API auth | Session authentication + `IsAdminUser` baseline | Implemented; Django admin removed |
| API namespace | allauth uses `/_allauth/` and `/accounts/`; staff namespace belongs to its owning Phase | Account paths done |
| Secrets/settings | Required secrets fail fast outside test; example env documents local values | Mostly done; final production image/env validation pending |
| Tests | Account contract, staff auth, core behavior, migrations and coverage gate | PostgreSQL suite (29 tests, 96.60% coverage) and migration checks passed; final CI pending |
| Docs checkpoint | `docs/build-plan.md` checkpoint and completion history match code and validation evidence | Current checkpoint updated; completion history waits for merge/final validation |

## Required Decisions Before Phase 1

1. Kakao social login:
   Console/basic login evidence exists; finish both cross-route flows with actual DB counts.
2. Client account integration:
   Complete email/password/Kakao browser QA in `../traceback-client`.
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

1. Complete actual cross-route Kakao/email browser QA and browser logout acceptance; server logout tests and QA cleanup passed.
2. Verify production same-origin proxy and SMTP configuration.
3. Verify production image build and final CI before marking Phase 0 complete; PostgreSQL tests passed.
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


## Final server verification (2026-09-13)

- PostgreSQL 17: `docker compose exec -T -e
  DJANGO_SETTINGS_MODULE=config.settings.test app pytest` passed all 29 tests,
  coverage 96.60% against the unchanged 90% gate. The test database was created
  with migrations and removed by pytest. Both cross-route account-count checks,
  logout session-row deletion/final 401, and password-change session invalidation
  passed. OAuth responses are mocked; actual Kakao cross-route browser QA remains.
- Live PostgreSQL `migrate --check`, `makemigrations --check --dry-run`, and
  Django system check passed.
- QA cleanup committed atomically: deleted synthetic User IDs 4–7 and their four
  EmailAddress rows, plus one referencing legacy `usersessions_usersession` row.
  Exact IDs/emails were checked before deletion; all other User and SocialAccount
  fields were compared before/after and preserved. No table was dropped.
  Final live counts: User 1 (ID 8), SocialAccount 1 (Kakao), Django Session 0.
- Ruff check/format, mypy (31 files), YAML lint, uv lock check, development
  Compose configuration, and diff checks passed. After the user updated Docker
  Desktop, production Compose config passed on v5.5.1. The resolved configuration
  contains only app, with no development DB, build, bind mount, published ports,
  or development dependencies. The existing overlay was preserved.
- An initial programmatic pytest invocation loaded Django before coverage began:
  29 tests passed but coverage was 84.50%. The standard pytest invocation above
  corrected this measurement error without changing code or lowering the gate.
- Server implementation and PostgreSQL QA are complete. Production container/proxy/
  SMTP validation, actual Kakao cross-route browser QA, and final CI remain for
  the overall Phase 0 verdict. The client was not modified in this run.
- The user approved the one-time 30-file limit exception for this 42-file
  server transition on 2026-09-13. Commit/push are authorized.

- 2026-09-13 follow-up: production image build passed (`traceback-production:qa`,
  image `3b0265b218b2`); updated Compose v5.5.1 configuration validation passed.
  A direct production container smoke subsequently passed with image
  `traceback-production-smoke:local` (`7a696a1a2b19`): Gunicorn booted all three
  workers and `/health` returned HTTP 200 under the `app` user, read-only root
  filesystem, init, and `no-new-privileges`. Runtime environment values were
  injected locally and were not embedded in the image or stored in Docker Hub.
  Reverse proxy/SMTP checks remain; the 42-file exception is approved.

- A prior session could not create `.git/index.lock`. Git write access was
  restored, and the authorized server commit/push completed in this session.
