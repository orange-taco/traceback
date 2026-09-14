# Current Work

새 세션은 이 문서를 현재 상태와 다음 행동의 단일 진입점으로 사용한다.
세부 계약은 관련 기준 문서에서만 관리한다.

## Current State

- Phase: Phase 0 — Foundation
- Backend branch: `phase-0c-account-auth-contract`
- Current slice: django-allauth Headless server authentication completion
- Server implementation, PostgreSQL contract tests, production image, and direct
  production container smoke are complete.
- Client 구현과 실제 Kakao browser acceptance는 별도 후속 작업이다.
- Phase 1 Catalog는 Phase 0의 남은 검증 전에는 시작하지 않는다.

## Implemented Contract

- Email signup, mandatory email verification, login, logout, password reset,
  password change, and Kakao OAuth use django-allauth Headless.
- Unverified email users can request a new confirmation link through the custom
  Headless endpoint `POST /_allauth/browser/v1/auth/email/verify/resend`.
  Responses do not reveal whether an address exists, and allauth's confirmation
  cooldown/rate limit remains active.
- Browser authentication uses Django database sessions. The browser stores an
  HttpOnly `sessionid`; mutating requests use Django CSRF protection.
- Kakao requests only verified `account_email`. Optional nickname/image scopes
  are not requested or copied into User columns.
- A verified provider email may connect to the matching User. New Kakao signup
  requires a verified email; an existing provider identity may re-login without it.
- allauth owns `EmailAddress` and `SocialAccount`; legacy account auth models were
  migrated and removed by `accounts.0004`.
- React Router uses same-origin `/_allauth` and `/accounts` routes. Production
  proxying must preserve the original Host and `X-Forwarded-Proto`.
- Staff API permissions use Django sessions with `IsAdminUser`. Django admin and
  SimpleJWT are not part of the current contract.

## Configuration Contract

- `ACCOUNT_LOGIN_METHODS = {"email"}`
- `ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]`
- `ACCOUNT_EMAIL_VERIFICATION = "mandatory"`
- Password minimum: 8 characters
- Email confirmation lifetime: 1 day
- Email confirmation send limit: 2 per 3 minutes per email and 3 per minute per IP
- Headless client: browser only
- Local frontend: `http://localhost:5173`
- Local provider callback: `http://localhost:8000/accounts/kakao/login/callback/`

## Validation

- Commit `818e8e9`: remote CI Quality, Test, and CodeRabbit checks passed.
- Current cleanup command `DJANGO_SETTINGS_MODULE=config.settings.test
  TRACEBACK_DATABASE_URL=sqlite:///:memory: uv run pytest` ran the full local
  suite: 32 tests passed with 96.37% coverage, including resend rate limits.
- PostgreSQL command `docker compose exec -T -e
  DJANGO_SETTINGS_MODULE=config.settings.test app pytest` passed 29 tests with
  96.60% coverage before the current cleanup. OAuth provider responses were mocked.
- A fresh migration run passed. A separate migration fixture with
  `Case@Test.com` and `case@test.com` stopped at `accounts.0003` with the intended
  clear case-insensitive duplicate error, before allauth lowercased User emails.
- Live PostgreSQL Django check, migration application/drift checks, Ruff,
  formatting, mypy, YAML lint, uv lock, and development/production Compose
  configuration passed.
- Production image `traceback-production-smoke:local` (`7a696a1a2b19`) booted
  Gunicorn as the `app` user with a read-only root filesystem and returned HTTP
  200 from `/health`. Runtime secrets were injected and were not embedded in the image.
- Synthetic QA Users 4–7, their EmailAddress rows, and one referencing legacy
  session row were removed. User 8 and its Kakao SocialAccount were preserved.

## Remaining Validation

1. Complete the current CodeRabbit follow-up and confirm remote CI.
2. Verify the production same-origin reverse proxy and real SMTP delivery.
3. In the separate client slice, complete password-change UI and actual Kakao
   cross-route browser acceptance, including logout and PostgreSQL row counts.
4. Record Phase 0 completion in `docs/build-plan.md` only after these checks pass.

## Client Handoff

- Add the password-change screen using
  `POST /_allauth/browser/v1/account/password/change`. Support social-only users
  setting their first password without `current_password`.
- Run social signup → password reset → email login → Kakao re-login and verified
  email signup → Kakao auto-connect in a real browser.
- Await logout before reading the session again and verify the final unauthenticated
  state and HttpOnly cookie behavior.
- Follow `../traceback-client/AGENTS.md`; keep client changes in that repository.

## Relevant Docs

- Phase/checkpoint: [`../build-plan.md`](../build-plan.md)
- API contract: [`../api-spec.md`](../api-spec.md)
- Models and column purposes: [`../domain-model.md`](../domain-model.md)
- Runtime and deployment: [`../infrastructure-decisions.md`](../infrastructure-decisions.md)
- Commands: [`../../README.md`](../../README.md)
