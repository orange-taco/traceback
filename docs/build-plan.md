# TRACEBACK Build Plan

이 문서는 Phase 범위와 완료 기준만 관리한다. 시스템 결정은 [`system.md`](system.md),
현재 상태는 [`current/README.md`](current/README.md)에 둔다.

## Phase 0 — Foundation

목표:

- Django/DRF 기본 구조와 공통 API 기반
- custom User와 allauth Headless email/password 인증
- mandatory email verification, password reset/change
- Kakao OAuth, provider 연결/해제, account deletion
- PostgreSQL 개발·운영 계약과 same-origin browser session
- client auth flow와 실제 브라우저 QA

완료 기준:

- 현재 코드·테스트·문서가 인증 계약과 일치한다.
- backend full test, Ruff, format, mypy, Django check, migration drift check가 통과한다.
- client typecheck/build와 실제 Kakao cross-route QA가 통과한다.
- development/production EC2에서 동일 ECR image digest 배포, reverse proxy,
  SMTP, CI 검증이 통과한다.
- 완료 커밋/PR과 남은 위험이 `docs/current/README.md`에 기록된다.

현재 남은 Phase 0 작업:

- client password-change 및 Kakao browser QA
- AWS development/production 이미지 승격과 reverse proxy/SMTP 검증
- 최종 remote CI 확인

## Phase 1 — Catalog

Phase 0 완료 후 시작한다.

- Category, Product, VariantGroup, Variant, image, size guide, banner, SiteSetting
- 고객 catalog API와 staff 상품 관리 API
- 재고/품절 계산의 최초 구현

## Later phases

- Cart/checkout/order
- Payment/webhook/refund
- Fulfillment/return
- Preorder, coupon, notification, CS, address 등

각 Phase 시작 시 필요한 모델·API·상태 전이를 그때 확정한다. 미래 기능을 현재 모델이나
문서에 미리 상세 설계하지 않는다.

## Working rule

- 한 task는 하나의 검증 가능한 slice로 끝낸다.
- task가 끝나면 상태 문서와 커밋/검증 결과를 남기고 AI 세션을 종료한다.
- 다음 task는 새 AI 세션에서 `current/README.md`와 `system.md`를 다시 읽고 시작한다.
