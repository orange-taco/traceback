# Current Work

이 문서는 새 세션에서 현재 작업을 빠르게 이어가기 위한 최소 컨텍스트다.
세부 설계나 완료 판정이 필요할 때만 상위 `docs/` 문서를 추가로 읽는다.

## 지금 상태

- 진행 단계: Phase 0 - Foundation
- 현재 브랜치: `phase-0b-common-api-auth`
- 현재 슬라이스: Phase 0B - account/auth and common API foundation
- 현재 코드 상태: Phase 0B 로컬 구현과 테스트는 완료됐고, 커밋/PR/실제 CI 증거는 아직 없음
- 파일 예산: 한 슬라이스 최대 30개
- Phase 1 Catalog 시작 금지: Phase 0 완료 기준이 통과하고 `docs/build-plan.md` 완료 이력에 기록되기 전까지 Catalog 작업을 시작하지 않는다.

## 다음 작업

Phase 0B 변경분을 리뷰하고 커밋/PR로 올린 뒤 실제 CI 결과를 확인한다.

현재 구현된 범위:

- custom User/Auth 모델
- account enum 분리: `SocialProvider`, `UserTokenPurpose`, `BenefitClaimCode`
- Kakao/Naver `SocialAccount`
- `EmailChangeRequest`
- `UserToken`
- `BenefitClaim`
- request ID middleware
- 공통 DRF 오류 응답
- 공통 pagination
- `/api/v1/admin/` 관리자 REST 인증 baseline
- 앱별 `urls.py` include 구조. `api_urls.py`와 `admin_urls.py`는 사용하지 않고, staff/admin REST surface는 `apps.console`에서 묶는다.
- 관련 테스트
- Phase 0B 모델/컬럼 목적 HTML 문서

남은 작업:

- 변경 diff 리뷰
- 필요하면 PostgreSQL 환경에서 migrate/test 재검증
- 커밋 또는 PR 생성
- CI migration 검증 증거 확인

## 이미 결정된 것

- Django/DRF/PostgreSQL을 사용한다.
- custom User는 `AbstractBaseUser` + `PermissionsMixin` 기반이고 email로 로그인한다.
- `User.REQUIRED_FIELDS = []`는 DB 컬럼이 아니라 Django custom user 설정이다. `createsuperuser`가 email/password 외 추가 필드를 묻지 않게 하며, username은 manager가 자동 생성한다.
- `UserManager.create_user()`는 저장 전에 `full_clean(exclude=["password"])`를 실행한다. manager 경로의 User 생성은 모델 필드/unique/constraint validation을 먼저 통과해야 한다.
- account enum은 model 내부 class가 아니라 `apps/accounts/enums.py`에 둔다.
- Django migration 파일은 생성물이므로 Ruff pre-commit check/format 대상에서 제외한다. 스키마 검증은 `makemigrations --check --dry-run`, `migrate`, 테스트로 한다.
- 관리자 REST 인증은 Django session + DRF `IsAdminUser`를 사용한다.
- 관리자 REST namespace는 `/api/v1/admin/`이다.
- 앱의 상위 `urls.py`는 하위 URL 묶음을 `include()`로 연결하고, viewset이 필요한 지점에서만 `DefaultRouter`를 둔다.
- staff/admin REST URL은 도메인 앱 내부 `staff` 패키지에 넣지 않고 `apps.console` 아래에 둔다. 도메인 모델과 운영자 API surface를 분리하기 위한 결정이다.
- `SiteSetting`은 Phase 0B에서 만들지 않는다. Phase 1 Catalog 또는 Phase 3 Order에서 재검토한다.
- `IdempotencyRecord`는 Phase 0B에서 만들지 않는다. Phase 3 Order 전에 재결정한다.
- `UserToken` 만료:
  - email verify: 24시간
  - password set: 1시간
  - password reset: 1시간
- `EmailChangeRequest`는 24시간 뒤 만료하고 같은 user 기준 10분에 1회 요청을 허용한다.
- `BenefitClaim`은 원문 개인정보 없이 HMAC hash ledger로 장기 보관한다.
- `User.deleted_at`, `SocialAccount.deleted_at`, `SocialAccount.anonymized_at` 컬럼은 탈퇴/익명화 정책을 표현하기 위해 유지한다.
- 실제 탈퇴 처리 메서드나 service는 Phase 0B MVP에서 만들지 않는다. 회원 탈퇴 API/운영 플로우가 시작될 때 구현한다.

## 먼저 확인할 것

작업 전:

```bash
git status --short --branch
```

이미 사용자 변경이 있으면 보존한다.

현재 작업 중 변경 파일 수는 신규 파일 포함 28개다. 30-file slice limit 안에 있다.

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
