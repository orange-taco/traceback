# Traceback API Spec

> 현재 구현 범위는 [`build-plan.md`](./build-plan.md)를 따른다. 이 문서는 외부 요청/응답 계약의 기준이다.

## 공통 정책

- Account authentication paths: `/_allauth/browser/v1` and `/accounts`
- Format: JSON, 금액은 KRW 정수
- staff 운영 인증: DRF staff API 기본 권한 후보는 `User.is_staff`를 확인하는 `IsAdminUser`이다. 세부 권한/namespace는 해당 Phase에서 확정한다.
- 리스트 응답: pagination 포함
- 오류 응답: `code`, `message`, `details`, `request_id`
- 생성/승인/취소 등 명령 API는 `Idempotency-Key`를 사용한다.
- 같은 scope/key와 같은 요청은 기존 결과, 다른 요청은 `409 Conflict`.
- 고객 명령 token 원문은 응답에만 포함하고 서버에는 hash만 저장한다.

DRF view convention:

- Resource API는 `GenericViewSet` + mixin 조합으로 만들고 router에 등록한다. mixin method를 오버라이드하면 DRF 원본 흐름(`get_serializer`, `perform_*`, pagination, headers)을 유지한다.
- Signup, token obtain, token refresh, callback처럼 resource CRUD가 아닌 단일 행위 API는 `GenericAPIView` 또는 해당 DRF 제공 view를 사용한다.
- 새 코드에서 `@api_view`, `APIView`, `ListAPIView`, `RetrieveAPIView`, `@action`은 사용하지 않는다.
- `GenericAPIView`는 class attribute(`permission_classes`, `authentication_classes`, `serializer_class`)를 먼저 두고, `serializer_class` 대상은 `self.get_serializer(...)`로 생성한다.
- Serializer는 `ModelSerializer`를 우선 사용한다. plain `Serializer`는 모델과 직접 매핑되지 않는 입력에만 사용한다. `Meta.fields`는 한 줄에 하나씩 명시한다.
- 응답 body가 있으면 serializer를 통과한다. DRF 제공 view는 제공 serializer와 응답 구조를 그대로 우선 사용한다.

계산 상태 enum:

- `order_status`: `pending`, `expired`, `paid`, `preparing`, `partially_shipped`, `shipped`, `delivered`, `cancelled`, `partially_returned`, `returned`
- `payment_status`: `pending`, `processing`, `paid`, `partially_refunded`, `refunded`, `cancelled`
- `fulfillment_status`: `unfulfilled`, `preparing`, `partially_shipped`, `shipped`, `delivered`

## 고객 API

### Account

회원 기능은 선택 흐름이며 Store, Cart, Checkout, Order Tracking은 비회원도 사용할
수 있어야 한다.

확정된 기준:

- django-allauth Headless Browser API가 가입, 이메일 인증, 로그인, 로그아웃,
  비밀번호 재설정, Kakao OAuth와 계정 연결을 담당한다.
- 인증 완료 상태는 Django DB session으로 저장하고 HttpOnly `sessionid` cookie로
  전달한다. JWT와 browser token storage는 사용하지 않는다.
- 변경 요청은 Django CSRF cookie와 `X-CSRFToken` header를 사용한다.
- 이메일 가입은 mandatory verification이며 확인 전에는 로그인을 완료할 수 없다.
- 비밀번호는 Django validators를 사용하며 최소 길이는 8자다.
- 이메일 확인과 비밀번호 재설정 링크는 frontend route로 발송한다.
- 검증된 provider email은 같은 email의 User를 인증하고 `SocialAccount`를 자동
  연결한다. 미검증 local email 선점 상태라면 allauth가 기존 password를
  무효화한 뒤 provider 소유자를 인증한다.
- Kakao가 verified email을 제공하지 않으면 가입/연결을 완료하지 않으며 별도
  email 입력을 받지 않는다.
- Kakao OAuth `state`, authorization code 교환, provider 오류 처리는 allauth가
  담당한다.

주요 allauth Browser API:

| Method / Path | 계약 |
| --- | --- |
| `GET /_allauth/browser/v1/config` | CSRF cookie와 client 설정 |
| `GET /_allauth/browser/v1/auth/session` | 현재 인증 상태와 User |
| `POST /_allauth/browser/v1/auth/signup` | `email`, `password`; 확인 메일 발송 |
| `POST /_allauth/browser/v1/auth/email/verify` | `key`; email 확인 및 session 완료 |
| `POST /_allauth/browser/v1/auth/login` | `email`, `password`; DB session 생성 |
| `DELETE /_allauth/browser/v1/auth/session` | 현재 session 종료 |
| `POST /_allauth/browser/v1/auth/password/request` | reset link 발송 |
| `POST /_allauth/browser/v1/auth/password/reset` | `key`, `password`; password 변경 |
| `POST /_allauth/browser/v1/account/password/change` | 로그인 및 CSRF 필요; `current_password`, `new_password`; allauth 기본 API |
| `POST /_allauth/browser/v1/auth/provider/redirect` | Kakao authorize redirect 시작 |
| `GET /accounts/kakao/login/callback/` | Kakao provider callback |

운영 프록시는 `/_allauth`와 `/accounts`를 같은 public origin에서 Django로
전달하고 원래 Host와 `X-Forwarded-Proto`를 보존한다.

### Catalog

| Method / Path | 계약 |
| --- | --- |
| `GET /home` | 활성 banner, best/new 상품 카드, 공개 site setting 반환 |
| `GET /products` | VariantGroup 카드 pagination. 필터 `category`, 정렬 `sort`. 카드: IDs/slugs, display name, min/max price, primary image, soldout |
| `GET /products/{slug}` | Product와 하위 활성 VariantGroup 요약 |
| `GET /products/{product_slug}/{variant_group_slug}` | Product/VariantGroup 상세, 이미지, Editor.js detail content, 활성 Variant, size guide, 배송 정책 |

재고 노출:

- Variant: `id`, `option_name`, `unit_price`, `purchase_type`, `preorder_expected_ship_at?`, `purchasable_qty`, `is_soldout`
- Phase 9+ 전에는 프리오더 Variant를 구매할 수 없어야 한다.

### Cart

익명 장바구니는 `traceback_cart` Secure/HttpOnly/SameSite=Lax cookie로 식별한다. 변경 요청은 CSRF 방어를 적용한다.

| Method / Path | 요청 | 응답 / 규칙 |
| --- | --- | --- |
| `GET /cart` | 없음 | cart와 item 목록, subtotal |
| `POST /cart/items` | `variant_id`, `quantity` | 동일 Variant는 수량 증가, 갱신 cart 반환 |
| `PATCH /cart/items/{item_id}` | `quantity` | 갱신 cart 반환 |
| `DELETE /cart/items/{item_id}` | 없음 | `204` |

Cart item 응답은 `id`, `variant_id`, `display_name`, `unit_price`, `quantity`, `line_amount`, `purchasable`을 포함한다.

### Order

#### `POST /orders`

- `Idempotency-Key` 필수.
- 요청: `cart_id?`, `customer`, `shipping_address`, `items[{variant_id, quantity}]`, `coupon_code(null only)`, `payment_method`.
- `cart_id`가 있으면 현재 cart 전체와 items가 정확히 일치해야 한다.
- 가격/할인/배송비/재고는 서버가 계산한다.
- Phase 3 범위에서는 in-stock만 허용한다.
- 응답: 주문 ID/번호/금액, `guest_access_token`, 최초 `payment` 객체.
- payment 객체: `id`, `provider`, `provider_order_id`, `client_token`, `client_token_expires_at`.
- 0원 주문은 payment confirm 없이 paid 상태로 반환한다.

#### `POST /orders/lookup`

- 요청: `order_number`, `phone`.
- 존재 여부를 구분하지 않는 실패 응답과 rate limit을 적용한다.
- 응답: `order_number`, `guest_access_token`, `expires_at`.

#### `GET /orders/{order_number}`

- 회원 소유권 또는 guest access bearer token 필요.
- 응답: 주문번호, 계산 상태 3종, `expired_at`, `fulfillment_on_hold`, 금액, lines/payments/fulfillments, 생성 시각.

#### `POST /orders/{order_number}/cancel`

- `Idempotency-Key`와 주문 접근 권한 필요.
- 배송 전 취소 가능한 잔여 수량 전체만 취소한다.
- shipped/delivered 수량이 있으면 `409`.
- 동기 완료는 `200`, PG 조정 중이면 `202`.
- 응답: 주문번호, 계산 주문/결제 상태, 환불 상태.

### Payment

#### `POST /payments/confirm`

- `Idempotency-Key`, `Authorization: Bearer {payment.client_token}` 필수.
- 요청: `payment_id`, `order_number`, `provider`, `payment_key`, `amount`.
- token/대상/금액/만료를 검증하고 PG 호출은 DB 트랜잭션 밖에서 수행한다.
- 완료는 `200`, 조정 중은 `202`.
- 응답: payment/order ID, 계산 결제/주문 상태, `fulfillment_on_hold`.

#### `POST /orders/{order_number}/payments`

- 주문 접근 권한과 `Idempotency-Key` 필요.
- 요청: `payment_method`, `provider`.
- 예약 유효 시간 안이고 성공/차단 승인 작업이 없을 때만 새 Payment를 만든다.
- 응답 `201`: 주문 생성 응답의 payment 객체.

#### `POST /payments/webhook`

- raw body 서명 검증 후 `provider + event_id`로 원문을 먼저 저장한다.
- 중복/순서 역전을 허용하고 공통 결제 조정 service로 처리한다.
- 오래 걸리는 후속 처리는 비동기로 넘긴다.

## Staff 운영 API

Django admin은 사용하지 않는다. Staff 운영 화면/API는 단일 client repo의 staff 화면에서 시작한다. DRF staff API 기본 권한 후보는 `IsAdminUser`이며, backend path, 세부 권한, 요청/응답 필드는 각 Phase 시작 전에 확정한다.

### Product / Inventory

| 기능 | 계약 후보 |
| --- | --- |
| 상품 목록 | 상품 pagination |
| 상품 생성 | Product와 VariantGroup/Variant 생성 |
| 상품 상세 | staff 상품 상세 |
| 상품 수정 | 상품/옵션 수정 |
| 상품 게시 | draft를 active로 게시 |
| 재고 조회 | 재고 필드와 계산 가용 수량 조회 |
| 재고 조정 | `Idempotency-Key`; 요청 `quantity_delta`, `reason`; row lock 후 movement 기록 |

### Order / Fulfillment

| 기능 | 계약 후보 |
| --- | --- |
| 주문 목록 | 계산 상태 필터를 지원하는 주문 pagination |
| 주문 상세 | snapshot, lines, payments, fulfillments, refunds/returns, active holds |
| 출고 보류 | `Idempotency-Key`; manual hold는 `reason`, `note` 필수 |
| 출고 보류 해제 | `Idempotency-Key`; 원천 상태 재검증 후 지정 hold 해제 |
| 출고 생성 | `Idempotency-Key`; 상태/송장/`lines[{order_line_id, quantity}]`; 출고 조건 검증 |
| 출고 상태 변경 | 준비/배송 상태 변경; shipped/delivered는 cancelled로 되돌리지 않음 |

### Cancellation / Refund

| 기능 | 계약 후보 |
| --- | --- |
| 주문 취소 | `Idempotency-Key`; 요청 `reason`, `lines[{order_line_id, quantity}]`; 결제 전 취소 또는 결제 후 환불 오케스트레이션 |
| 환불 생성 | `Idempotency-Key`; 완료 ReturnLine 기반 환불 또는 수기 조정 |
| 환불 재시도 | 기존 Refund와 PG 작업 키로 조회/재시도 |

규칙:

- shipped/delivered 수량은 취소할 수 없다.
- 결제 후 취소는 PG 호출 전에 hold, Refund/RefundLine, 단일 PaymentTransaction을 커밋한다.
- PG 성공 후에만 취소 수량과 재고 복구를 반영한다.
- 수기 조정은 전액 환불을 만들 수 없다.

### Return

| 기능 | 계약 후보 |
| --- | --- |
| 반품 접수 | `Idempotency-Key`; 배송 완료 수량 범위 안에서 접수 |
| 반품 상태 변경 | `Idempotency-Key`; `requested -> approved/rejected`, `approved -> in_transit/received`, `in_transit -> received` |
| 반품 완료 | `Idempotency-Key`; accepted/restock 수량 확정, 재판매 가능 수량만 재고 복구 |

환불은 자동 생성하지 않고 완료 Return을 참조해 별도 실행한다.

## Phase 9+

쿠폰, 회원, 프리오더 구매 등 확장 API는 해당 Phase 시작 시 이 문서에 추가한다. 구현 전에는 관련 입력을 명시적으로 거절한다.
