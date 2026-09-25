# TRACEBACK System

새 기능을 시작할 때 전체 구조와 이미 확정된 핵심 결정만 확인하는 문서다.
구현 세부사항과 과거 검증 로그는 코드·CI·커밋을 기준으로 확인한다.

## Task flow

새 AI 세션은 다음 순서로 작업한다.

```text
codebase check → system/design check → user decision review → implementation/test
```

코드베이스와 문서가 현재 요청과 맞지 않으면 먼저 상태를 확인한다. 제품·API·보안·
아키텍처·인프라처럼 의미가 바뀌는 결정은 구현 전에 사용자와 합의하고 이 문서 또는
`build-plan.md`에 기록한다. 한 task가 끝나면 세션을 닫고 다음 task는 새 세션에서 시작한다.

## Product shape

- 고객은 비회원으로 Store, Cart, Checkout, Order Tracking을 사용할 수 있다.
- 인증은 선택 기능이며, staff 운영 기능은 별도 client에서 제공한다.
- 금액은 KRW 정수로 저장한다.
- 상태는 가능한 경우 원천 데이터에서 계산하고, 중복 상태 컬럼은 만들지 않는다.

## Auth

- 인증: django-allauth Headless + Django DB session
- Browser cookie: HttpOnly `sessionid`; 변경 요청은 Django CSRF 사용
- Email: mandatory verification, allauth `EmailAddress`가 인증 상태 소유
- Social: allauth `SocialAccount`가 provider identity 소유
- Kakao: verified `account_email`만 사용하고 Admin Key server-side unlink
- Kakao unlink 성공 후 로컬 account state를 atomic하게 정리한다.
- Kakao `-101`은 이미 unlink된 상태이므로 성공으로 처리한다.
- 사용자 세션은 `allauth.usersessions`로 사용자별 조회·종료한다.
- SocialAccount 연결 해제의 검증·삭제 흐름은 allauth Headless endpoint를 사용한다.
- 계정 전체 삭제는 `/accounts/delete`에서 provider unlink 후 User를 비활성·익명화한다.

## Catalog

- `Category → Product → ProductVariantGroup → ProductVariant` 구조다.
- 고객 목록/PDP의 단위는 VariantGroup이고, 구매 단위는 Variant다.
- 상품은 `draft / active / archived` 상태를 가진다.
- 일반 재고: `stock - reserved - safety_stock`
- 프리오더는 별도 예약/확정 수량을 사용하며 초기 MVP에서는 구매를 허용하지 않는다.
- 이미지, 사이즈 가이드, 배너, 운영 SiteSetting은 Catalog 영역에 속한다.

## Cart and order

- 익명 Cart는 HttpOnly cookie의 token을 사용하며 DB에는 hash만 저장한다.
- Cart/Order/Payment/Inventory/Refund/Fulfillment 원천 데이터를 기준으로 상태를 계산한다.
- 주문 생성은 Variant lock + 재고 검증 + Order snapshot + 예약 movement를 하나의 DB transaction으로 처리한다.
- 외부 PG 호출은 DB transaction 밖에서 수행하고, `PaymentTransaction`을 작업 기록으로 사용한다.
- Payment confirm, webhook, polling은 동일한 조정 service와 idempotency key를 공유한다.
- 고객 명령은 `IdempotencyRecord`, PG webhook은 `PaymentEvent`, 재고 변경은 `InventoryMovement`로 멱등성을 보장한다.
- 취소·환불·반품은 수량과 금액의 원천 행을 잠근 뒤 처리한다.
- 배송 완료 수량은 반품으로만 되돌리고, 출고·환불·재고 reconciliation hold가 있으면 추가 출고를 막는다.

## Infrastructure

- Python/dependency: `uv` + `pyproject.toml` + `uv.lock`
- Development: Docker Compose PostgreSQL, local file storage
- Staging/production: AWS, managed PostgreSQL, S3-compatible storage
- App: Gunicorn + Uvicorn worker + Django ASGI
- Runtime: EC2 + Docker Compose, production image는 ECR에서 배포
- Migration: CI는 임시 DB에서 검증하고, 실제 환경의 `migrate --noinput`은 CD에서 새 애플리케이션 실행 전에 수행한다.
- Branch flow: feature → `development` → `main`
- Secrets: untracked environment/secret store; repository에는 placeholder만 둔다.
- AWS 환경별 `.env`는 각 서버에서 관리하고, Git에는 `.env.dev.git`/`.env.prod.git` 템플릿만 둔다. Compose는 서버의 `.env`를 app 컨테이너에 전달한다.
- CI는 GitHub-hosted runner를 사용한다.
- Local email은 console mailer로 출력하고, AWS 환경은 SES SMTP(STARTTLS, 587)를 사용한다.

## Deferred

- Celery/background job과 queue는 비동기 작업이 실제로 필요할 때 도입한다.
- abandoned account cleanup은 가입 완료 상태·보존 기간·정리 범위를 먼저 확정한 뒤 추가한다.
- Coupon, notification, CS, address, preorder 상세는 해당 Phase에서 결정한다.
- AWS network, ECR lifecycle, S3/CDN, secret rotation, APM 상세는 staging 전 확정한다.
