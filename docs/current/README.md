# Current Work

이 문서는 새 세션에서 현재 작업을 빠르게 이어가기 위한 최소 컨텍스트다.
세부 설계나 완료 판정이 필요할 때만 상위 `docs/` 문서를 추가로 읽는다.

## 지금 상태

- 진행 단계: Phase 0 - Foundation
- 현재 브랜치: `phase-0c-account-auth-contract`
- 현재 슬라이스: Phase 0C - account API surface
- 현재 코드 상태: Phase 0B account/auth foundation은 `development`에 merge됨. PR #6도 `development`에 merge되어 DRF view convention과 account auth 결정 지점 문서화가 반영됨. 0C-1 email/password session API는 이 브랜치에서 구현됨. 고객 social/email verification/password reset API는 아직 구현하지 않음
- 프론트 상태: `../traceback-client` 컨벤션은 `AGENTS.md`에 정리 완료. React Router v8 기준이며, 프론트 작업 전 반드시 `../traceback-client/AGENTS.md`, `docs/brand-concept.md`, `docs/wireframe.md`를 읽는다.
- 파일 예산: 한 슬라이스 최대 30개
- Phase 1 Catalog 시작 금지: Phase 0 완료 기준이 통과하고 `docs/build-plan.md` 완료 이력에 기록되기 전까지 Catalog 작업을 시작하지 않는다.

## 다음 작업

Phase 0C의 현재 브랜치에는 email/password first 기준의 backend session API가
구현되어 있다. 다음 작은 슬라이스는 social login 서버 계약과 구현이다. Kakao/Naver
OAuth start/callback, provider user lookup, `SocialAccount` 생성/재사용, session login,
성공/실패 frontend redirect 계약을 확정한 뒤 구현한다.

다음 세션에서 바로 해야 할 일:

1. 백엔드와 클라이언트 작업트리를 각각 확인한다.
2. 클라이언트 작업이 포함되면 `../traceback-client/AGENTS.md`와 관련 docs를 먼저 읽는다.
3. social login을 Kakao만 먼저 자를지 Kakao/Naver를 같은 슬라이스에 넣을지 결정한다.
4. social start/callback, 성공/실패 redirect, auto-linking 실패 응답 정책을 문서화하고 구현한다.
5. 구현 후 백엔드 테스트와 프론트 typecheck/build, Playwright 또는 in-app browser QA를 수행한다.
6. 프론트 QA는 Design / UX / Function으로 나누어 사용자 확인을 받는다.

Phase 0B에서 구현된 범위:

- custom User/Auth 모델
- account enum 분리: `SocialProvider`, `UserTokenPurpose`, `BenefitClaimCode`
- Kakao/Naver `SocialAccount`
- `EmailChangeRequest`
- `UserToken`
- `BenefitClaim`
- request ID middleware
- 공통 DRF 오류 응답
- 공통 pagination
- `/api/accounts/admin/` 관리자 REST 인증 baseline
- Phase 0B 관리자 REST surface는 accounts URL에서 묶는다.
- 관련 테스트
- Phase 0B 모델/컬럼 목적 HTML 문서

완료된 Phase 0C 범위:

- DRF convention 문서화
- 기존 function-based account view 제거
- `/api/accounts/admin/session`을 `APIView`로 전환
- 고객 account API 구현 전 확정해야 할 기준 문서화
- 프론트 컨벤션은 `../traceback-client/AGENTS.md`에 정리 완료
- email/password session API backend 구현:
  - `POST /api/accounts/signup`
  - `POST /api/accounts/login`
  - `GET /api/accounts/session`
  - `POST /api/accounts/logout`
  - 공통 user 응답 `{id, email, username, email_verified}`
  - signup/login 성공 시 Django session cookie 생성
  - session 조회 시 anonymous도 `200`으로 `{authenticated:false, user:null}` 반환
  - login 실패는 email 존재 여부를 드러내지 않는 공통 오류 반환

다음 슬라이스 후보:

- Kakao social login backend vertical slice
- Naver social login backend vertical slice
- social login 성공/실패 frontend redirect 연동
- 이메일 인증 발송 시스템 결정
- email verification과 welcome benefit 지급 조건 결정
- password set은 기존 비밀번호가 없는 사용자도 허용
- password reset은 이메일 링크 기반으로 구현
- account auth frontend signup/login/session/logout 연동

## 이미 결정된 것

- Django/DRF/PostgreSQL을 사용한다.
- custom User는 `AbstractBaseUser` + `PermissionsMixin` 기반이고 email로 로그인한다.
- `User.REQUIRED_FIELDS = []`는 DB 컬럼이 아니라 Django custom user 설정이다. `createsuperuser`가 email/password 외 추가 필드를 묻지 않게 하며, username은 manager가 자동 생성한다.
- `UserManager.create_user()`는 저장 전에 `full_clean(exclude=["password"])`를 실행한다. manager 경로의 User 생성은 모델 필드/unique/constraint validation을 먼저 통과해야 한다.
- account enum은 model 내부 class가 아니라 `apps/accounts/enums.py`에 둔다.
- Django migration 파일은 생성물이므로 Ruff pre-commit check/format 대상에서 제외한다. 스키마 검증은 `makemigrations --check --dry-run`, `migrate`, 테스트로 한다.
- 관리자 REST 인증은 Django session + DRF `IsAdminUser`를 사용한다.
- 관리자 REST namespace는 `/api/accounts/admin/`이다.
- DRF view convention:
  - 2개 이상의 mixin/action 조합으로 자연스럽게 표현되는 resource API는 `ViewSet`을 사용한다.
  - 단일 행위 endpoint로만 표현되는 API는 `APIView`를 사용한다.
  - `@api_view`, `GenericAPIView`, `ListAPIView`, `RetrieveAPIView` 등 나머지 view 형태는 새 코드에서 사용하지 않는다.
  - account/auth처럼 로그인, 로그아웃, 이메일 인증, 비밀번호 재설정, 소셜 완료는 resource CRUD가 아니므로 기본적으로 `APIView` 대상이다.
  - catalog/admin resource처럼 목록/상세/생성/수정/삭제 중 2개 이상이 필요한 경우 `ViewSet` 대상이다.
  - `APIView`는 class attribute로 필요한 `permission_classes`, `authentication_classes`, `serializer_class`, `response_serializer_class`를 먼저 드러내고 HTTP method handler를 둔다.
  - 응답 shape는 view의 ad hoc dict helper가 아니라 serializer 또는 serializer가 소비하는 명시적 DTO를 SSOT로 둔다.
- 앱의 상위 `urls.py`는 실제 하위 URL이 필요한 앱에만 둔다.
- Phase 0B staff/admin REST URL은 별도 `staff` 패키지 없이 accounts URL에서 시작한다.
- `SiteSetting`은 Phase 0B에서 만들지 않는다. Phase 1 Catalog 또는 Phase 3 Order에서 재검토한다.
- `IdempotencyRecord`는 Phase 0B에서 만들지 않는다. Phase 3 Order 전에 재결정한다.
- `UserToken` 만료:
  - email verify: 24시간
  - password set: 1시간
  - password reset: 1시간
- `EmailChangeRequest`는 24시간 뒤 만료하고 같은 user 기준 10분에 1회 요청을 허용한다.
- `BenefitClaim`은 원문 개인정보 없이 HMAC hash ledger로 장기 보관한다.
- Phase 0C account API는 email/password 가입과 로그인을 먼저 구현한다.
- 고객 account 인증은 Django session cookie를 사용한다.
- email/password signup/login 성공 시 같은 session 응답을 반환하고 session cookie를 생성한다.
- `GET /api/accounts/session`은 anonymous도 200으로 반환하며 CSRF cookie를 설정한다.
- `POST /api/accounts/logout`은 현재 session을 제거하고 204를 반환한다.
- social login도 성공 시 같은 session cookie와 session 응답 계약을 사용한다.
- 이메일 인증은 필요하지만 사용할 이메일 발송 시스템을 아직 정하지 않았다.
- password set은 기존 비밀번호가 없는 사용자도 사용할 수 있어야 한다.
- password reset은 이메일 링크 기반으로 구현한다.
- `UserToken`, `EmailChangeRequest`, `BenefitClaim`의 실제 발급/소비 API와 클라이언트 연동 flow는 클라이언트 구현 시점에 구현한다.
- `User.deleted_at`, `SocialAccount.deleted_at` 컬럼은 탈퇴/익명화 정책을 표현하기 위해 유지한다.
- 실제 탈퇴 처리 메서드나 service는 Phase 0B MVP에서 만들지 않는다. 회원 탈퇴 API/운영 플로우가 시작될 때 구현한다.

## 먼저 확인할 것

작업 전:

```bash
git status --short --branch
```

이미 사용자 변경이 있으면 보존한다.

현재 백엔드 작업 브랜치는 `phase-0c-account-auth-contract`이다. 클라이언트는 마지막
확인 기준 `migrate-react-router-v8` 브랜치이며 `.gitignore` 수정이 남아 있었다. 프론트
작업을 시작하기 전 해당 변경이 사용자 작업인지 확인하고 보존한다.

## 필요한 경우만 읽을 문서

- Phase 0B 모델/컬럼 목적: [`phase-0b-model-purpose.html`](./phase-0b-model-purpose.html)
- Phase 0B 상세 결정: [`../phaseB.md`](../phaseB.md)
- Phase 0 완료 기준: [`../phase-0-completion.md`](../phase-0-completion.md)
- 전체 체크포인트와 완료 이력: [`../build-plan.md`](../build-plan.md)
- 전체 구현 원칙: [`../simple-build-guide.md`](../simple-build-guide.md)
- API 공통 규약 확인이 필요할 때: [`../api-spec.md`](../api-spec.md)
- User 모델 원칙 확인이 필요할 때: [`../domain-model.md`](../domain-model.md)

## 완료 전 검증

Phase 0 완료로 기록하기 전에는 `docs/phase-0-completion.md`의 command set을 실행한다.
검증이 끝나기 전에는 `docs/build-plan.md` 완료 이력에 완료로 적지 않는다.

마지막 로컬 검증:

- Phase 0B commit: `6a0b3d4`
- Phase 0B merge: PR #5, merge commit `489ed3b`
- Phase 0C DRF convention slice:
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_api_foundation.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy apps/accounts apps/core`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest`
  - `git diff --check`
- Phase 0C-1 email/password session API:
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/serializers.py apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_account_auth_api.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff format --check apps/accounts/serializers.py apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_account_auth_api.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy apps/accounts apps/core`
- Phase 0C-1 APIView/session serializer cleanup:
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/serializers.py apps/accounts/views.py apps/core/tests/test_account_auth_api.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy apps/accounts apps/core`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check .`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/migrations/0001_initial.py`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff format --check .`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy .`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py check`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py makemigrations --check --dry-run`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache TRACEBACK_DATABASE_URL=sqlite:////tmp/traceback-phase0b-check.sqlite DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py migrate --noinput`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache TRACEBACK_DATABASE_URL=sqlite:////tmp/traceback-phase0b-check.sqlite DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py migrate --check`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run yamllint .`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pre-commit validate-config`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pre-commit run ruff-check --files apps/accounts/migrations/0001_initial.py apps/accounts/models.py`
- `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pre-commit run ruff-format --files apps/accounts/migrations/0001_initial.py apps/accounts/models.py`
- `docker compose --env-file .env.example config --quiet`
- `APP_IMAGE=traceback:test docker compose --env-file .env.example -f docker-compose.yml -f docker-compose_prod.yml config --quiet`

아직 못 돌린 검증:

- PostgreSQL 실환경 migrate/test
- production image build
- 실제 GitHub Actions CI

## 작업 종료 시 업데이트

작업을 마치거나 세션을 멈추기 전에는 이 문서를 현재 코드 상태에 맞게 갱신한다.

반드시 갱신할 내용:

- 지금 상태: phase, 브랜치, 현재 슬라이스가 실제와 일치하는지
- 다음 작업: 새 세션이 바로 시작할 수 있는 가장 구체적인 행동
- 이미 결정된 것: 작업 중 새로 확정된 설계 결정
- 먼저 확인할 것: 남은 사용자 변경, 미검증 파일, 주의할 충돌
- 완료 전 검증: 마지막으로 통과한 명령과 아직 못 돌린 명령

`docs/build-plan.md`의 재개 체크포인트도 같은 내용으로 맞춘다. 단, 완료 이력은
완료 조건과 검증이 실제로 끝난 뒤에만 기록한다.
