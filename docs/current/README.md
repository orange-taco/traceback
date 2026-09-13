# Current Work

새 세션은 이 문서를 단일 진입점으로 사용한다. 세부 계약을 변경할 때만 아래
관련 문서를 추가로 읽는다.

## Current State

- Phase: Phase 0 - Foundation
- Backend branch: `phase-0c-account-auth-contract`
- Client branch: `phase-0c-client-auth`
- Current slice: django-allauth Headless server authentication completion
- Scope decision (2026-09-13): finish server work first; client implementation
  and browser UI acceptance are a separate follow-up, not blockers for server
  implementation completion. Real PostgreSQL/server verification remains required.
- Backend transition, production Compose configuration, and direct production
  container smoke are verified. Client work is a separate follow-up.
- Phase 1 Catalog must not start until Phase 0 completion criteria are recorded.

## Implemented

- Python 3.14 and Django 6.1 runtime baseline.
- Custom email-based `accounts.User` and phone-based `BenefitClaim` ledger.
- django-allauth Headless email signup, mandatory email verification, login,
  logout, password reset, and Kakao OAuth.
- Django database sessions with HttpOnly session cookies; SimpleJWT and browser
  token storage are removed.
- Verified provider email may authenticate and connect to the matching User.
  For an unverified local email, allauth invalidates the old password before
  accepting the verified social login.
- allauth owns `EmailAddress` and `SocialAccount`; the legacy account token,
  email-change-request, and social-account models are removed by migration.
- React Router uses same-origin `/_allauth` and `/accounts` requests. Vite
  proxies both paths to Django locally.
- Staff API permission probes use Django sessions and `IsAdminUser`.

## Auth Contract

- Browser session authority: Django/allauth only.
- Email signup is incomplete until the email link is confirmed.
- Signup and login password minimum: 8 characters.
- New Kakao signup requires a verified provider email, without a fallback
  email form. An already linked Kakao identity can re-login without email.
- Kakao scopes: `account_email`, `profile_nickname`, `profile_image`.
- Local frontend: `http://localhost:5173`
- Local allauth callback:
  `http://localhost:8000/accounts/kakao/login/callback/`
- Production proxy must route `/_allauth` and `/accounts` to Django while
  preserving the original Host and `X-Forwarded-Proto`.

## Current QA checkpoint (2026-09-13)

Server implementation, PostgreSQL contract tests, migration checks, and scoped
QA-account cleanup are complete. See Final server verification below.
The actual Kakao browser cross-route flows remain separate acceptance work:
previous basic login returned User ID 8 with an HttpOnly cookie, but the browser
logout follow-up raced the request and the MCP transport disconnected.
The server contract test now verifies logout DB-row removal and final HTTP 401.

## Remaining validation and next action

1. Check remote CI for the committed and pushed server changes. The 42-file
   exception is approved; production image and container smoke pass.
2. In the separate client follow-up, complete the handoff below and actual Kakao
   cross-route acceptance with PostgreSQL counts.
3. Verify production container/reverse proxy/SMTP and final CI before recording
   overall Phase 0 completion. Do not start Phase 1 yet.

## Client handoff — deferred from this server slice

1. Add an authenticated password-change screen and an Account-page link.
   Call `POST /_allauth/browser/v1/account/password/change` with
   `current_password` and `new_password`, using the existing same-origin
   session and CSRF helper. Add new-password confirmation, submitting state,
   validation messages, and handling for an expired session. For social-only
   users without a password, allauth accepts setting a password without
   `current_password`; the screen must account for that existing API behavior.
2. Complete MCP Playwright QA: social signup → password reset email → email
   login → Kakao re-login, and verified email signup → Kakao auto-connect.
   Coordinate DB row-count checks with the backend. Verify provider-error UI
   for missing/unverified email and already-linked re-login behavior.
3. Await the logout response before fetching the session again; verify final
   unauthenticated state and HttpOnly cookies. The previous concurrent fetch
   did not establish the final logout result.
4. Run client typecheck/build after implementation, then remove that run's QA
   records and temporary Playwright files. Preserve existing unrelated changes.

## Relevant Docs

- Completion/checkpoint: [`build-plan.md`](../build-plan.md),
  [`phase-0-completion.md`](../phase-0-completion.md)
- Account API: [`api-spec.md`](../api-spec.md)
- Models and migrations: [`domain-model.md`](../domain-model.md),
  [`account-model-purpose.md`](./account-model-purpose.md)
- Runtime and proxy: [`infrastructure-decisions.md`](../infrastructure-decisions.md)
- Auth/infrastructure status: [`auth-status-map.html`](./auth-status-map.html)
- Commands: [`commands.md`](../commands.md)


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
