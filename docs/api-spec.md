# Traceback API Spec

> 현재 구현 범위는 [`build-plan.md`](./build-plan.md)를 따른다. 이 문서는 외부 요청/응답 계약의 기준이다.

## 공통 정책

- Accounts base path: `/api/accounts`
- Format: JSON, 금액은 KRW 정수
- 관리자 인증: Django session + staff/superuser + DRF `IsAdminUser`
- 리스트 응답: pagination 포함
- 오류 응답: `code`, `message`, `details`, `request_id`
- 생성/승인/취소 등 명령 API는 `Idempotency-Key`를 사용한다.
- 같은 scope/key와 같은 요청은 기존 결과, 다른 요청은 `409 Conflict`.
- 고객 명령 token 원문은 응답에만 포함하고 서버에는 hash만 저장한다.

계산 상태 enum:

- `order_status`: `pending`, `expired`, `paid`, `preparing`, `partially_shipped`, `shipped`, `delivered`, `cancelled`, `partially_returned`, `returned`
- `payment_status`: `pending`, `processing`, `paid`, `partially_refunded`, `refunded`, `cancelled`
- `fulfillment_status`: `unfulfilled`, `preparing`, `partially_shipped`, `shipped`, `delivered`

## 고객 API

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

## 관리자 API

모든 관리자 API는 session 인증과 `IsAdminUser`를 요구한다. 각 Phase 시작 전 요청/응답 세부 필드를 확정한다.

### Product / Inventory

| Method / Path | 계약 |
| --- | --- |
| `GET /admin/products` | 상품 pagination |
| `POST /admin/products` | Product와 VariantGroup/Variant 생성 |
| `GET /admin/products/{id}` | 관리자 상품 상세 |
| `PATCH /admin/products/{id}` | 상품/옵션 수정 |
| `POST /admin/products/{id}/publish` | draft를 active로 게시 |
| `GET /admin/variants` | 재고 필드와 계산 가용 수량 조회 |
| `POST /admin/variants/{id}/inventory-adjustments` | `Idempotency-Key`; 요청 `quantity_delta`, `reason`; row lock 후 movement 기록 |

### Order / Fulfillment

| Method / Path | 계약 |
| --- | --- |
| `GET /admin/orders` | 계산 상태 필터를 지원하는 주문 pagination |
| `GET /admin/orders/{id}` | snapshot, lines, payments, fulfillments, refunds/returns, active holds |
| `POST /admin/orders/{id}/fulfillment-hold` | `Idempotency-Key`; manual hold는 `reason`, `note` 필수 |
| `POST /admin/fulfillment-holds/{id}/release` | `Idempotency-Key`; 원천 상태 재검증 후 지정 hold 해제 |
| `POST /admin/orders/{id}/fulfillments` | `Idempotency-Key`; 상태/송장/`lines[{order_line_id, quantity}]`; 출고 조건 검증 |
| `PATCH /admin/fulfillments/{id}` | 준비/배송 상태 변경; shipped/delivered는 cancelled로 되돌리지 않음 |

### Cancellation / Refund

| Method / Path | 계약 |
| --- | --- |
| `POST /admin/orders/{id}/cancellations` | `Idempotency-Key`; 요청 `reason`, `lines[{order_line_id, quantity}]`; 결제 전 취소 또는 결제 후 환불 오케스트레이션 |
| `POST /admin/refunds` | `Idempotency-Key`; 완료 ReturnLine 기반 환불 또는 수기 조정 |
| `POST /admin/refunds/{id}/retry` | 기존 Refund와 PG 작업 키로 조회/재시도 |

규칙:

- shipped/delivered 수량은 취소할 수 없다.
- 결제 후 취소는 PG 호출 전에 hold, Refund/RefundLine, 단일 PaymentTransaction을 커밋한다.
- PG 성공 후에만 취소 수량과 재고 복구를 반영한다.
- 수기 조정은 전액 환불을 만들 수 없다.

### Return

| Method / Path | 계약 |
| --- | --- |
| `POST /admin/orders/{id}/returns` | `Idempotency-Key`; 배송 완료 수량 범위 안에서 접수 |
| `PATCH /admin/returns/{id}` | `Idempotency-Key`; `requested -> approved/rejected`, `approved -> in_transit/received`, `in_transit -> received` |
| `POST /admin/returns/{id}/complete` | `Idempotency-Key`; accepted/restock 수량 확정, 재판매 가능 수량만 재고 복구 |

환불은 자동 생성하지 않고 완료 Return을 참조해 별도 실행한다.

## Phase 9+

쿠폰, 회원, 프리오더 구매 등 확장 API는 해당 Phase 시작 시 이 문서에 추가한다. 구현 전에는 관련 입력을 명시적으로 거절한다.
