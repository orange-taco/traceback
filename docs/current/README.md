# Current Work

이 문서는 새 세션에서 현재 작업을 빠르게 이어가기 위한 단일 진입점이다.
먼저 이 문서로 현재 상태와 다음 행동을 확인하고, 세부 설계나 완료 판정이
필요할 때만 아래 "필요한 경우만 읽을 문서"에서 해당 문서를 추가로 읽는다.

## 지금 상태

- 진행 단계: Phase 0 - Foundation
- 현재 브랜치: `phase-0c-account-auth-contract`
- 현재 슬라이스: Phase 0C - account API surface
- 현재 코드 상태: Phase 0B account/auth foundation은 `development`에 merge됨. PR #6도 `development`에 merge되어 DRF view convention과 account auth 결정 지점 문서화가 반영됨. 0C-1 email/password JWT account API는 이 브랜치에서 구현됨. 고객 social/email verification/password reset API는 아직 구현하지 않음
- 프론트 상태: `../traceback-client`는 현재 초기 storefront/wireframe 상태이고 account auth 연동은 아직 없음. 현재 확인 기준으로 client repo에는 `AGENTS.md`가 없으므로, 프론트 작업 전 client-side 작업 규칙 파일을 만들거나 복구한 뒤 `../traceback-client/docs/brand-concept.md`, `../traceback-client/docs/wireframe.md`와 함께 읽는다.
- 파일 예산: 한 슬라이스 최대 30개
- Phase 1 Catalog 시작 금지: Phase 0 완료 기준이 통과하고 `docs/build-plan.md` 완료 이력에 기록되기 전까지 Catalog 작업을 시작하지 않는다.

## 다음 작업

Phase 0C의 현재 브랜치에는 email/password first 기준의 backend JWT account API가
구현되어 있다. 이 PR은 문서 정합성을 맞춘 뒤 마무리한다.

다음 구현 순서는 social login backend를 먼저 자르고, 그 다음 client account 연동으로
간다. 초기 social provider 범위는 기존 결정대로 Kakao/Naver이며, 다음 슬라이스는
Kakao부터 시작한다. Google은 현재 Phase 0 결정 범위에 없으므로 추가하려면 별도
범위 결정이 필요하다.

다음 세션에서 바로 해야 할 일:

1. 이 브랜치에서 stale 문서 문구를 정리하고 PR #7을 마무리한다.
2. 다음 백엔드 브랜치를 `development`에서 만들고 Kakao social login backend vertical slice를 시작한다.
3. Kakao Developers 설정값을 확인한다: REST API key, client secret 사용 여부, backend callback URL, frontend 성공/실패 redirect URL.
4. `api-spec.md`에 Kakao start/callback path, provider env var, 성공/실패 redirect, existing email auto-linking 실패 응답 정책을 기록하고 구현한다.
5. Kakao backend 검증 후 client 작업 규칙 파일을 정리하고 `../traceback-client`에서 social/email account 연동을 진행한다.
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
- 관리자 REST 인증 정책 baseline
- Phase 0B 관리자 REST surface는 accounts URL에서 묶는다.
- 관련 테스트
- Phase 0B 모델/컬럼 목적 HTML 문서

완료된 Phase 0C 범위:

- DRF convention 문서화
- 기존 function-based account view 제거
- 관리자 REST 인증은 JWT Bearer token + `IsAdminUser` 기준으로 정리
- 고객 account API 구현 전 확정해야 할 기준 문서화
- client account auth 연동은 아직 시작하지 않음
- email/password JWT account API backend 구현:
  - `POST /api/accounts/signup`
  - `POST /api/accounts/token/obtain`
  - `POST /api/accounts/token/refresh`
  - signup 성공 시 `201`과 빈 응답 반환
  - token obtain 성공 시 JWT access/refresh token pair 반환
  - token obtain 실패는 SimpleJWT 기본 `no_active_account` 오류 반환

다음 슬라이스 후보:

- Kakao social login backend vertical slice
- Naver social login backend vertical slice
- social login 성공/실패 frontend redirect 연동
- client 작업 규칙 파일 생성/복구
- account auth frontend signup/token obtain/token refresh 연동
- 이메일 인증 발송 시스템 결정
- email verification과 welcome benefit 지급 조건 결정
- password set은 기존 비밀번호가 없는 사용자도 허용
- password reset은 이메일 링크 기반으로 구현

## 이미 결정된 것

- Django/DRF/PostgreSQL을 사용한다.
- custom User는 `AbstractBaseUser` + `PermissionsMixin` 기반이고 email로 로그인한다.
- `User.REQUIRED_FIELDS = []`는 DB 컬럼이 아니라 Django custom user 설정이다. `createsuperuser`가 email/password 외 추가 필드를 묻지 않게 하며, username은 manager가 자동 생성한다.
- `UserManager.create_user()`는 저장 전에 `full_clean(exclude=["password"])`를 실행한다. manager 경로의 User 생성은 모델 필드/unique/constraint validation을 먼저 통과해야 한다.
- `UserManager.get_by_natural_key()`는 email을 앞뒤 공백 제거 후 소문자로 정규화하고 `deleted_at is null`인 사용자만 로그인 lookup 대상으로 삼는다.
- account enum은 model 내부 class가 아니라 `apps/accounts/enums.py`에 둔다.
- Django migration 파일은 생성물이므로 Ruff pre-commit check/format 대상에서 제외한다. 스키마 검증은 `makemigrations --check --dry-run`, `migrate`, 테스트로 한다.
- 관리자 REST 인증은 JWT Bearer token + DRF `IsAdminUser`를 사용한다.
- 관리자 REST namespace는 `/api/accounts/admin/`이다. 실제 admin resource endpoint는 해당 Phase에서 추가한다.
- DRF view convention:
  - Resource API는 `GenericViewSet` + mixin 조합으로 만들고 router에 등록한다. mixin method를 오버라이드하면 DRF 원본 흐름(`get_serializer`, `perform_*`, pagination, headers)을 유지한다.
  - Signup, token obtain, token refresh, callback처럼 resource CRUD가 아닌 단일 행위 API는 `GenericAPIView` 또는 해당 DRF 제공 view를 사용한다.
  - 새 코드에서 `@api_view`, `APIView`, `ListAPIView`, `RetrieveAPIView`, `@action`은 사용하지 않는다.
  - `GenericAPIView`는 class attribute(`permission_classes`, `authentication_classes`, `serializer_class`)를 먼저 두고, `serializer_class` 대상은 `self.get_serializer(...)`로 생성한다.
  - Serializer는 `ModelSerializer`를 우선 사용한다. plain `Serializer`는 모델과 직접 매핑되지 않는 입력에만 사용한다. `Meta.fields`는 한 줄에 하나씩 명시한다.
  - 응답 body가 있으면 serializer를 통과한다. DRF 제공 view는 제공 serializer와 응답 구조를 그대로 우선 사용한다.
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
- 고객 account 인증은 JWT Bearer token을 사용한다.
- email/password signup은 `201`과 빈 응답을 반환한다.
- email/password token obtain/refresh는 SimpleJWT 제공 view를 그대로 사용한다.
- token obtain 성공 시 JWT access/refresh token pair를 반환한다.
- `POST /api/accounts/token/refresh`는 refresh token으로 새 access token을 반환한다.
- social login도 성공 시 JWT access/refresh token pair를 반환한다.
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
확인 기준 `development` 브랜치이고 작업트리는 clean이다. 프론트 작업을 시작하기 전
다시 작업트리를 확인하고, client repo에 없는 `AGENTS.md`를 만들거나 복구한다.

## 필요한 경우만 읽을 문서

평소에는 이 문서만 읽고 시작한다. 아래 문서는 작업이 해당 영역을 건드릴 때만 연다.

- Phase/완료 판정 기록을 바꿀 때: [`../build-plan.md`](../build-plan.md), [`../phase-0-completion.md`](../phase-0-completion.md)
- API endpoint, 요청/응답, 오류 계약을 구현할 때: [`../api-spec.md`](../api-spec.md)
- 모델, migration, 제약 조건을 바꿀 때: [`../domain-model.md`](../domain-model.md), [`phase-0b-model-purpose.html`](./phase-0b-model-purpose.html)
- Phase 0B 결정 배경이 필요할 때: [`../phaseB.md`](../phaseB.md)
- 주문/결제/재고 흐름을 구현할 때: [`../order-flow.md`](../order-flow.md)
- 인프라, 배포, 환경변수를 바꿀 때: [`../infrastructure-decisions.md`](../infrastructure-decisions.md)
- 명령어 목록이 필요할 때: [`../commands.md`](../commands.md)
- 전체 원칙을 다시 확인할 때: [`../simple-build-guide.md`](../simple-build-guide.md)

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
- Phase 0C-1 email/password JWT account API:
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/serializers.py apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_account_auth_api.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff format --check apps/accounts/serializers.py apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_account_auth_api.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy apps/accounts apps/core`
- Phase 0C-1 GenericAPIView convention alignment:
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/models.py apps/accounts/serializers.py apps/accounts/views.py apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff format --check apps/accounts/models.py apps/accounts/serializers.py apps/accounts/views.py apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy apps/accounts apps/core`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py`
  - `git diff --check`
- Phase 0C-1 JWT auth transition:
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check apps/accounts/managers.py apps/accounts/serializers.py apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py config/settings/base.py config/settings/test.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff format --check apps/accounts/managers.py apps/accounts/serializers.py apps/accounts/views.py apps/accounts/urls.py apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py config/settings/base.py config/settings/test.py`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy apps/accounts apps/core config/settings/base.py config/settings/test.py`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest apps/core/tests/test_account_auth_api.py apps/core/tests/test_api_foundation.py`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run python manage.py check`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run python manage.py makemigrations --check --dry-run`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv lock --check`
  - `git diff --check`
- PR #7 review follow-up:
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff check .`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run ruff format --check .`
  - `UV_CACHE_DIR=/tmp/traceback-uv-cache uv run mypy .`
  - `DJANGO_SETTINGS_MODULE=config.settings.test TRACEBACK_DATABASE_URL=sqlite:///:memory: UV_CACHE_DIR=/tmp/traceback-uv-cache uv run pytest`
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
