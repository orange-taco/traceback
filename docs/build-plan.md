# Traceback Build Plan

> 상위 문서: [`../main.md`](../main.md). 이 문서가 구현 순서, 현재 범위, 완료 판정의 단일 기준이다.

## 재개 체크포인트

- 진행 단계: Phase 0 — Foundation
- 현재 브랜치: `phase-0-foundation`
- 현재 작업 슬라이스: Phase 0A — scaffold
- 슬라이스 목표: Django/DRF/PostgreSQL 프로젝트와 환경 설정, `/api/v1` 및 health check 기반 구성
- 변경 파일 예산: 이번 설정 기반 슬라이스는 사용자 승인으로 30개 제한 예외
- 관련 명세: `phase-0-completion.md`, `api-spec.md` 공통 규약/health check, `domain-model.md` 공통 원칙
- 현재까지 완료: Bootstrap A — Docker/Compose, Phase 0A Django/DRF scaffold와 DefaultRouter/health check, `uv`/Ruff/mypy/yamllint/pytest/coverage/CI, CodeRabbit/Dependabot/pre-commit, `development` → `main` production ECR/EC2 CD workflow
- 확인된 결정: Django/DRF/PostgreSQL, `uv` + lockfile, Gunicorn + Uvicorn worker + ASGI, development(local)/staging(AWS)/production(AWS), development 기본 Compose + production 공통 overlay, 로컬 Compose PostgreSQL, AWS EC2 + Docker Compose + managed PostgreSQL, 로컬 파일 저장소와 staging/production S3
- 미해결/설계 의심: Phase 0 전체 완료 조건 중 공통 오류 응답, pagination, request ID, 관리자 REST 인증, `SiteSetting`, `IdempotencyRecord` 구현이 아직 확인되지 않음. `User`는 기본 `auth.User` 유지 또는 커스텀 User 도입 결정을 Phase 1 전에 확정해야 함
- 다음 작업: Phase 0B — common API/auth
- 정확한 다음 행동: `docs/phase-0-completion.md` 기준으로 `User` 결정을 먼저 확정하고, Phase 0B 공통 오류 응답, pagination, request ID, 관리자 REST 인증, 공통 모델을 `development` 대상 PR로 구현한다. Phase 0 완료 전 Phase 1 Catalog를 시작하지 않는다.
- 마지막 검증: 2026-07-06 Django 5.2.15 설치 확인, `uv run pytest` 통과, `uv run python manage.py check --settings=config.settings.test` 통과. 기본 development 설정의 `manage.py check`는 `DJANGO_SECRET_KEY` 미주입 시 실패.

이 섹션은 세션 재개를 위한 영속 상태다. 새 세션이 추가 질문 없이 다음 행동을 수행할 수 있을 정도로 유지한다.

## 완료 이력

완료된 작업만 아래 표에 추가한다. 시작했지만 완료 조건을 통과하지 못한 작업은 추가하지 않고 재개 체크포인트에 유지한다.

| 슬라이스 | 완료 커밋/PR | 검증 증거 | 설계 변경 |
| --- | --- | --- | --- |
| Bootstrap A — Docker/Compose | `45bd637` | development/production `docker compose config`, development/production app target 빌드, `git diff --check` | 없음 |

완료 판정:

- 슬라이스 완료 조건과 관련 테스트가 통과했다.
- 실제 동작과 문서가 일치한다.
- 설계 의심과 미검증 사항이 남아 있지 않다.
- 변경 파일 수가 30개 이하다.
- 완료 커밋 또는 PR 식별자가 기록되어 있다.

진행 상태 해석:

- **완료**: 완료 이력에 기록됨.
- **진행 중/중단됨**: 재개 체크포인트의 현재 작업 슬라이스에 기록됨.
- **미착수**: 완료 이력과 현재 작업 슬라이스에 없고, 아래 Phase 계획에만 존재함.
- **막힘**: 재개 체크포인트의 미해결/설계 의심에 차단 원인과 필요한 결정이 기록됨.

## 작업 방식

Phase 안에서 작업 슬라이스를 시작할 때 "재개 체크포인트"를 갱신한다.

```text
진행 단계:
현재 브랜치:
현재 작업 슬라이스:
슬라이스 목표:
변경 파일 예산:
관련 명세:
현재까지 완료:
확인된 결정:
미해결/설계 의심:
다음 작업:
정확한 다음 행동:
마지막 검증:
```

설계 문제가 발견되면:

1. 체크포인트의 "미해결/설계 의심"에 기대 동작, 실제 동작, 영향 범위를 기록한다.
2. 구현 버그 / 명세 오류 / 새 제약 / 범위 변경으로 분류한다.
3. 데이터 정합성, 복구 가능성, API 호환성, 구현 비용을 기준으로 결정한다.
4. 설계 문제면 `api-spec.md`, `domain-model.md`, `order-flow.md` 중 영향받는 문서를 먼저 수정한다.
5. Phase 범위, 코드, 테스트를 결정된 설계에 맞춘다.
6. 테스트와 실제 API로 다시 검증하고 체크포인트에 결정과 증거를 기록한다.

PR 피드백도 같은 기준으로 분류한다. 피드백이 API 계약, 모델/제약, 상태 흐름, Phase 범위를 바꾸면 설계 문제로 처리해 영향받는 상세 문서를 수정한다. 단순 구현 품질 피드백은 관련 코드와 테스트만 수정한다.

## 작업 슬라이스 / PR 규칙

- 한 슬라이스는 독립적으로 검증 가능하고 PR 하나로 제출 가능한 단위다.
- 한 슬라이스/PR의 변경 파일은 추가·수정·삭제·migration·문서를 포함해 최대 30개다.
- 예상 파일 수가 30개를 넘으면 구현 전에 슬라이스를 나눈다.
- Phase 완료는 여러 PR로 구성할 수 있다.
- 각 PR은 관련 테스트와 필요한 문서 동기화를 포함해야 한다.
- 세션 종료 시 미완료 코드가 있어도 체크포인트에 완료 지점, 미검증 사항, 정확한 다음 행동을 남긴다.
- 최초 Docker/Compose 부트스트랩은 `main` 직접 작업 예외다. 이후 슬라이스는 `development` 기반 PR 규칙을 따른다.

권장 분할 예:

- Bootstrap: `Docker/Compose on main` → `development 생성`
- Foundation: `0A scaffold` → `0B common API/auth` → `0C core models/CI`
- Catalog: `1A models/admin` → `1B customer read API`
- Order 이후: 모델/마이그레이션 → service/동시성 → API → 경합/멱등 테스트

## 선결 결정

Docker/Compose 부트스트랩 결정:

- Dockerfile은 루트의 단일 `Dockerfile`만 사용한다.
- `docker-compose.yml`은 로컬 development 서비스/네트워크/볼륨/command/bind mount/port의 기준 파일이다.
- `docker-compose_prod.yml`은 production command, restart/resource/security 설정과 운영 환경값을 추가/재정의하고 로컬 bind mount/port/PostgreSQL service를 제거한다.
- 개발 실행은 `docker compose ...` 형식을 사용한다.
- 운영 실행은 `docker compose -f docker-compose.yml -f docker-compose_prod.yml ...` 형식을 사용한다.
- 비밀값은 Compose 파일에 직접 저장하지 않는다.

Phase 0 결정:

- 관리자 REST 인증: Django session 인증 + `is_staff`/`is_superuser` + DRF `IsAdminUser`
- DB: PostgreSQL
- 관리자 REST API는 Django admin과 별도로 구현하며 Django admin은 운영 보조 수단으로 사용

다음 결정은 해당 Phase 시작 전에 확정한다.

| 시점 | 결정 |
| --- | --- |
| Phase 1 | Phase 9+ 전까지 프리오더 상품의 노출/구매 차단 계약 |
| 각 관리자 API Phase | 요청/응답, 권한, 주요 오류 계약 |
| Phase 4 | 최초 PG, 지원 결제수단, sandbox, webhook 검증 방식 |
| Phase 4 | 예약 만료 후 지연 승인 시 최소 안전 조정과 자동 보상 범위 |

## Phase 시작 조건

- 선결 결정이 해결되어 있다.
- 관련 API의 요청/응답, 인증, 오류, 멱등성 요구가 구현 가능한 수준이다.
- 관련 모델/흐름의 필드, 제약, 트랜잭션, 동시성 보호가 정의되어 있다.
- 완료 조건을 검증할 핵심 테스트가 정해져 있다.

## Bootstrap A — Docker/Compose

- **브랜치**: `main` 직접 작업. 이 부트스트랩 완료 후 `development` 생성.
- **파일**: 단일 `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `docker-compose_prod.yml`, 필요한 환경변수 예시/실행 문서.
- **공통 Compose**: 애플리케이션과 PostgreSQL 서비스, named volume, healthcheck, 공통 네트워크/환경변수 계약.
- **Development 기본 구성**: bind mount, 개발 command, 개발 port, 로컬 PostgreSQL.
- **운영 Overlay**: 운영 command, 자동 재시작, 운영 노출/보안 설정. 소스 bind mount 금지.
- **완료**:
  - `docker compose config` 성공
  - `docker compose -f docker-compose.yml -f docker-compose_prod.yml config` 성공
  - 단일 Dockerfile로 두 환경 이미지 구성이 가능
  - 비밀값이 저장소 파일에 포함되지 않음
  - 변경 파일 30개 이하
  - 완료 상태를 `main`에 커밋한 뒤 그 커밋에서 `development` 생성

## Phase 0 — Foundation

- **범위**: Django/DRF/PostgreSQL 프로젝트, 환경 설정, `User`, `SiteSetting`, `IdempotencyRecord`, `/api/v1`, health check, 공통 오류, pagination, `request_id`, 관리자 인증, CI.
- **검증**: 설정/비밀키 주입, namespace 분리, 관리자 권한, 공통 응답 규약.
- **완료**: 새 환경에서 설치, migrate, 테스트가 성공하고 CI가 같은 검증을 실행한다.
- **참고**: `phase-0-completion.md`, `api-spec.md` 기본/응답 정책, `domain-model.md` User/SiteSetting/IdempotencyRecord.

## Phase 1 — Catalog

- **범위**: Catalog 모델과 Banner, 고객 home/상품 API, 관리자 상품 CRUD/publish API.
- **재고**: `InventoryMovement` 없이 Variant 원시 수량으로 구매 가능 수량을 계산한다.
- **검증**: VariantGroup 목록 노출 단위, 사이즈 가이드 JSON, Editor.js 상세, 이미지 primary, 하위 카테고리 필터.
- **완료**: 시드 데이터 고객 API와 관리자 상품 API가 명세대로 동작한다.
- **참고**: `domain-model.md` Catalog, `api-spec.md` 홈/상품/상품 관리.

## Phase 2 — Cart

- **범위**: `Cart`, `CartItem`, 비회원 장바구니 API.
- **검증**: HttpOnly cookie 식별, CSRF, 동일 Variant 수량 증분, 구매 가능 여부 재계산.
- **완료**: 쿠키 기반 조회/추가/수정/삭제와 품절 표시가 동작한다.
- **참고**: `domain-model.md` Cart, `api-spec.md` 장바구니.

## Phase 3 — Order + Inventory Reserve

- **범위**: 주문/스냅샷/라인, `InventoryMovement`, 최초 `Payment`, `OrderFulfillmentHold` 모델, 주문 생성, 관리자 재고 조회/조정.
- **제한**: `in_stock`, `coupon_code = null`, 단일 배송지, 전체 장바구니 전환 또는 바로구매.
- **검증**: 주문 스냅샷, 할인 배분 골격, 예약 movement, oversell 방지, 재고 조정 감사/멱등성, 주문 생성 멱등성, 0원 주문.
- **완료**: 주문 생성, 동시 주문, 멱등 재시도, 0원 결제 완료, 관리자 재고 조정 테스트가 통과한다.
- **참고**: `order-flow.md` 주문 생성/재고, `domain-model.md` Order/Inventory, `api-spec.md` 주문/재고 관리.

## Phase 4 — Payment

- **범위**: `PaymentTransaction`, `PaymentEvent`, confirm, webhook, 실패 후 새 Payment, 예약 만료 처리.
- **검증**: PG 호출 트랜잭션 경계, 중복 confirm/webhook, timeout 조정, 재고 확정 1회, 만료/승인 경합, 재시도 허용/거절.
- **완료**: 정상/실패/중복/timeout/경합 시나리오와 확정한 지연 승인 안전 조정 테스트가 통과한다.
- **참고**: `order-flow.md` 결제/예외, `domain-model.md` Payment, `api-spec.md` 결제.

## Phase 5 — Guest Order Access

- **범위**: 주문 lookup/detail, 배송 전 전체 취소.
- **검증**: 접근 토큰, rate limit, 존재 여부 비노출, 계산 상태, 예약 해제, `expired_at`.
- **완료**: 비회원 조회와 결제 전/후 배송 전 전체 취소가 동작한다.
- **참고**: `api-spec.md` 주문 조회/cancel, `order-flow.md` 취소/만료.

## Phase 6 — Fulfillment

- **범위**: 관리자 주문 조회, `Fulfillment`, `FulfillmentLine`, 출고 보류 set/release, 부분출고.
- **검증**: 결제/재고/hold 출고 조건, 동시 수량 검증, 부분출고.
- **완료**: 준비/송장/배송 완료, 부분출고, hold 차단/해제가 동작한다.
- **참고**: `order-flow.md` 운영자/부분출고, `domain-model.md` Fulfillment, `api-spec.md` 주문 관리.

## Phase 7 — Cancel / Refund

- **범위**: 관리자 부분취소, `Refund`, `RefundLine`, 환불 생성/재시도.
- **검증**: PG 호출 전 hold/transaction 커밋, 단일 환불 작업 재사용, 비례 환불 배분, 중복 환불 방지.
- **완료**: 부분취소/환불 정합성과 실패/중복/재시도 테스트가 통과한다.
- **참고**: `order-flow.md` 결제 완료 후 취소, `domain-model.md` Refund, `api-spec.md` cancellations/refunds.

## Phase 8 — Returns

- **범위**: 관리자 반품 접수/상태 변경/검수 완료, 재고 복구, 완료 반품 환불 연결.
- **검증**: 상태 전이, 반품 가능 수량, 인정/재입고 수량, 재판매 가능 수량만 복구.
- **완료**: 반품 접수부터 검수, 재고 복구, 별도 환불 연결까지 동작한다.
- **참고**: `order-flow.md` 반품, `domain-model.md` Return, `api-spec.md` 반품 관리.

## Phase 9+ — 확장

- 쿠폰
- 프리오더 구매/결제/입고 배정
- 지연 승인 자동 보상 환불 고도화
- 알림, CS, 회원, 리뷰, 찜, WMS, 교환, 다중 창고

## Phase 완료 체크

1. 검증할 가정마다 결과와 테스트 증거가 있다.
2. 발견한 설계 문제가 관련 문서, 코드, 테스트에 반영됐다.
3. migration과 자동화 테스트가 통과한다.
4. 실제 API가 `api-spec.md`와 일치한다.
5. 다음 Phase가 의존할 스키마와 계약을 안정화했다.
6. 모든 PR이 변경 파일 30개 이하이고 독립적으로 검증 가능하다.
7. 재개 체크포인트가 현재 코드 상태와 정확히 일치한다.
8. 완료 이력에 커밋/PR과 검증 증거를 기록했다.
