# Traceback Domain Model

> 현재 구현 범위는 [`build-plan.md`](./build-plan.md)를 따른다. 이 문서는 필드, 관계, DB 제약의 기준이다. 상태 전이와 재고 부호는 [`order-flow.md`](./order-flow.md), 외부 계약은 [`api-spec.md`](./api-spec.md)를 따른다.

## 공통 규칙

- 모든 모델은 별도 명시가 없으면 `id`, `created_at`, `updated_at`을 가진다.
- 금액은 KRW 정수, 수량은 0 이상의 정수다.
- 주문/결제/출고 전체 상태는 저장하지 않고 원천 데이터에서 계산한다.
- 여러 행 합계가 필요한 불변조건은 관련 행을 잠근 service layer에서 검증한다.

## Catalog

| 모델 | 주요 필드 | 핵심 규칙 |
| --- | --- | --- |
| `Category` | `parent_id?`, `name`, `slug`, `sort_order`, `is_visible` | `slug` unique, 고객 필터는 하위 카테고리 포함 |
| `Product` | `category_id`, `name`, `slug`, `status(draft/active/archived)`, `base_price`, `season`, `gender`, `published_at?` | `slug` unique, 상품군 단위 |
| `ProductSizeGuide` | `product_id`, `unit`, `columns JSON`, `guide_image_url?`, `note` | 상품당 최대 1개, columns가 측정항목 순서/라벨 소유 |
| `ProductSizeGuideRow` | `product_size_guide_id`, `size_label`, `measurements JSON`, `sort_order` | measurements key는 상위 columns code만 허용 |
| `ProductVariantGroup` | `product_id`, `name`, `slug`, `option_type`, `color_code?`, `description`, `detail_content JSON`, `is_active`, `sort_order` | `(product_id, slug)` unique, 고객 목록/PDP 노출 단위 |
| `ProductVariantGroupImage` | `variant_group_id`, `image_url`, `alt_text`, `is_primary`, `sort_order` | 그룹당 primary 최대 1개 |
| `ProductVariant` | `variant_group_id`, `option_name`, `sku_code?`, `unit_price`, `purchase_type(in_stock/preorder)`, `stock_qty`, `reserved_qty`, `safety_stock_qty`, `preorder_limit_qty?`, `preorder_reserved_qty`, `preorder_committed_qty`, `preorder_expected_ship_at?`, `is_active`, `sort_order` | `(variant_group_id, option_name)` unique, `sku_code` partial unique |
| `Banner` | `title`, `image_url`, `link_url`, `start_at`, `end_at`, `sort_order`, `is_active` | 활성 기간 내 고객 홈 노출 |
| `SiteSetting` | `brand_name`, `cs_phone`, `cs_kakao_url`, `default_courier_code`, `default_courier_name`, `shipping_fee`, `free_shipping_threshold`, `remote_area_extra_fee`, 배송/교환/반품/개인정보/약관 text, `product_listing_mode` | 단일 운영 설정으로 사용 |

재고 계산:

- 일반 상품: `purchasable_qty = max(stock_qty - reserved_qty - safety_stock_qty, 0)`
- 프리오더: `purchasable_qty = max(preorder_limit_qty - preorder_reserved_qty - preorder_committed_qty, 0)`
- `is_soldout = purchasable_qty <= 0`
- Phase 9+ 전에는 프리오더 구매를 허용하지 않는다.

## User / Cart

| 모델 | 주요 필드 | 핵심 규칙 |
| --- | --- | --- |
| `User` | `email`, `username`, `username_changed_at`, `name`, `phone_e164`, `phone_verified_at`, `email_verified_at`, `is_active`, `is_staff`, `is_superuser`, `deleted_at`, `last_login` | custom User, 정규화 email 로그인, 활성·비삭제 User만 로그인 lookup 대상, 탈퇴 시 email 익명화로 재가입 허용, `username` unique 자동 생성, 활성 인증 phone partial unique |
| `SocialAccount` | `user_id`, `provider(kakao/naver)`, `provider_user_id`, `provider_email`, `provider_email_verified`, `is_active`, `linked_at`, `deleted_at?` | active 행만 lookup, `(provider, provider_user_id)` unique, `(user_id, provider)` unique, 탈퇴 시 inactive + provider identity/email 익명화 |
| `EmailChangeRequest` | `user_id`, `new_email`, `token_hash`, `expires_at`, `confirmed_at?` | token 원문 저장 금지, 24시간 만료, user당 10분 1회 요청, 새 요청 시 기존 미확정 요청 만료 |
| `UserToken` | `user_id`, `purpose(email_verify/password_set/password_reset)`, `token_hash`, `expires_at`, `consumed_at?` | token 원문 저장 금지, email verify 24시간, password set/reset 1시간 만료 |
| `BenefitClaim` | `code`, `user_id?`, `phone_hash?`, `claimed_at`, `claim_source`, `metadata` | `welcome_signup`은 `phone_hash IS NOT NULL`이며 `(code, phone_hash)` unique, 원문 전화번호 저장 금지, HMAC hash ledger로 장기 보관 |
| `UserAddress` | `user_id`, 주소 필드, `is_default` | Phase 9+, 사용자당 default 최대 1개 |
| `Cart` | `user_id?`, `cart_token_hash?`, `status(active/ordered/expired)`, `expires_at?` | token hash partial unique, 회원당 active 최대 1개 |
| `CartItem` | `cart_id`, `product_variant_id`, `quantity` | `(cart_id, product_variant_id)` unique, `quantity > 0` |

익명 cart token 원문은 HttpOnly cookie로만 전달하고 DB에는 hash만 저장한다.

## Order

| 모델 | 주요 필드 | 핵심 규칙 |
| --- | --- | --- |
| `Order` | `order_number`, `user_id?`, `subtotal_amount`, `discount_amount`, `shipping_amount`, `total_amount`, `currency`, `reservation_expires_at?`, `expired_at?`, `guest_access_token_hash?`, `guest_access_token_expires_at?` | `order_number` unique, 전체 상태 저장 금지 |
| `OrderCustomerSnapshot` | `order_id`, `name`, `phone`, `email` | `order_id` unique |
| `OrderShippingAddress` | `order_id`, `recipient_name`, `recipient_phone`, `zonecode`, `road_address`, `jibun_address`, `detail_address`, `building_name`, `address_extra`, `delivery_message` | `order_id` unique |
| `OrderLine` | `order_id`, `product_variant_id`, 상품/옵션/SKU/이미지 snapshot, `purchase_type_snapshot`, `preorder_expected_ship_at_snapshot?`, `unit_price`, `quantity`, `cancelled_qty`, `returned_qty`, `discount_amount` | 단일 status 저장 금지 |
| `OrderFulfillmentHold` | `order_id`, `reason(payment_reconciliation/inventory_reconciliation/manual)`, `status(active/released)`, `note`, `created_by?`, `released_by?`, `released_at?` | `(order_id, reason)` active 최대 1개 |

금액:

- `subtotal_amount = sum(OrderLine.unit_price * quantity)`
- `discount_amount = sum(OrderLine.discount_amount)`
- `total_amount = subtotal_amount - discount_amount + shipping_amount`
- 할인은 대상 라인의 할인 전 금액 비율로 배분하고 나머지는 `OrderLine.id` 순으로 배분한다.

라인 수량:

- `shippable_qty = quantity - cancelled_qty`
- `kept_qty = quantity - cancelled_qty - returned_qty`
- `shipped_qty`: shipped/delivered FulfillmentLine 합계
- `delivered_qty`: delivered FulfillmentLine 합계
- `preparing_qty`: pending/preparing FulfillmentLine 합계
- cancelled Fulfillment의 라인은 집계에서 제외한다.

## Payment / Refund / Return

| 모델 | 주요 필드 | 핵심 규칙 |
| --- | --- | --- |
| `Payment` | `order_id`, `provider`, `method`, `amount`, `provider_order_id`, `client_token_hash?`, `client_token_expires_at?` | provider order ID/token hash partial unique, 주문당 여러 시도 허용 |
| `PaymentTransaction` | `payment_id`, `refund_id?`, `provider`, `transaction_type(authorize/capture/pay/cancel/refund/void)`, `idempotency_key?`, `status(pending/processing/waiting_for_deposit/success/failed/cancelled/expired)`, `provider_status?`, `amount`, `provider_transaction_id?`, 요청/응답/오류 필드, `requested_at`, `completed_at?`, `expires_at?` | 외부 PG 작업 단위 |
| `PaymentEvent` | `payment_id?`, `provider`, `event_id`, `event_type`, `headers`, `payload`, `signature_valid`, `processing_status`, `processed_at?` | `(provider, event_id)` unique |
| `Refund` | `order_id`, `payment_id`, `status(requested/approved/processing/completed/failed/rejected)`, `refund_type`, `amount`, `goods_refund_amount`, `shipping_refund_amount`, `adjustment_amount`, `reason`, `admin_memo`, `provider_refund_id?`, `requested_at`, `completed_at?` | PG 환불 조정 단위 |
| `RefundLine` | `refund_id`, `order_line_id`, `return_line_id?`, `quantity`, `refund_amount` | 취소/반품 대상 수량과 금액 귀속 |
| `Return` | `order_id`, `status(requested/approved/in_transit/received/rejected/completed)`, `reason`, `admin_memo`, 상태 시각 | 관리자 반품 처리 단위 |
| `ReturnLine` | `return_id`, `order_line_id`, `quantity`, `accepted_qty?`, `restock_qty`, `restock_note` | `0 <= restock_qty <= accepted_qty <= quantity` |

결제 계산:

- `paid_amount = sum(success pay/capture amount)`
- `completed_refund_amount = sum(completed Refund.amount)`
- 완료 환불액은 승인액을 초과할 수 없다.
- 0원 주문은 성공한 `internal/free pay`, 취소는 성공한 `internal void`로 구분한다.
- 하나의 Refund는 최대 하나의 `PaymentTransaction(refund_id)`를 소유하고 재시도 시 재사용한다.
- `Refund.amount = goods_refund_amount + shipping_refund_amount + adjustment_amount > 0`
- `Refund.goods_refund_amount = sum(RefundLine.refund_amount)`
- 수기 조정만으로 전액 환불을 만들 수 없다.

부분 환불액:

`refund_amount = floor(line_net_amount * q1 / quantity) - floor(line_net_amount * q0 / quantity)`

`q0`은 기존 완료 환불 수량, `q1`은 이번 완료 후 누적 수량이다.

## Inventory

`InventoryMovement` 필드:

- `product_variant_id`, `order_id?`, `order_line_id?`
- `bucket(on_hand/reserved/preorder_reserved/preorder_committed)`
- `movement_type(reserve/release/sale/cancel_restore/return_restore/manual_adjust/preorder_reserve/preorder_release/preorder_commit/preorder_cancel/preorder_allocate)`
- `quantity`, `quantity_before`, `quantity_after`
- `operation_key`, `correlation_id`, `reason`, `created_by?`

규칙:

- `operation_key` 전역 unique. 같은 이동 재실행은 기존 movement를 반환한다.
- 한 명령의 여러 bucket 이동은 같은 `correlation_id`를 사용한다.
- movement quantity는 bucket 필드의 실제 증감 부호다.

| 작업 | bucket | 부호 |
| --- | --- | ---: |
| 일반 예약 / 해제 | `reserved` | `+수량` / `-수량` |
| 일반 판매 / 취소·반품 복구 | `on_hand` | `-수량` / `+수량` |
| 프리오더 예약 / 해제·결제확정 | `preorder_reserved` | `+수량` / `-수량` |
| 프리오더 결제확정 / 취소·입고배정 | `preorder_committed` | `+수량` / `-수량` |
| 프리오더 입고배정 | `on_hand` | `-수량` |

## Fulfillment

| 모델 | 주요 필드 | 핵심 규칙 |
| --- | --- | --- |
| `Fulfillment` | `order_id`, `status(pending/preparing/shipped/delivered/cancelled)`, 택배/송장 필드, 상태 시각 | shipped/delivered는 취소로 되돌리지 않음 |
| `FulfillmentLine` | `fulfillment_id`, `order_line_id`, `quantity` | 활성 배정 합계는 `shippable_qty` 이하 |

## Idempotency

`IdempotencyRecord` 필드:

- `scope`, `key`, `request_hash`, `status(processing/completed/failed)`
- `resource_type?`, `resource_id?`, `response_status?`, `response_body?`, `expires_at`

규칙:

- `(scope, key)` unique.
- 같은 key + 같은 body는 기존 결과, 다른 body는 `409`.
- 민감 token 원문은 저장하지 않는다.
- 생성 재시도 token은 `scope + key + resource_id + secret version`으로 결정적 재생성한다.

## DB 제약

필수 check:

- `stock_qty >= reserved_qty`
- in-stock은 프리오더 필드 null/0, preorder는 `preorder_limit_qty > 0`이고 예약+확정이 한도 이하
- `Order.total_amount = subtotal_amount - discount_amount + shipping_amount`
- `OrderLine.quantity > 0`, `cancelled_qty + returned_qty <= quantity`
- Cart/Fulfillment/Refund/Return line quantity `> 0`
- waiting-for-deposit transaction은 `expires_at` 필수
- ReturnLine 수량 관계
- Refund 금액 구성 관계와 `amount > 0`

필수 service 불변조건:

- 활성 FulfillmentLine 합계는 `shippable_qty` 이하
- 진행/완료 ReturnLine 합계는 배송 완료 수량 이하
- 완료/선점 RefundLine 합계는 취소·반품 가능 수량 이하
- 성공 승인액/완료 환불액 상한
- 활성 hold 또는 진행 중 취소/환불이 있으면 신규 출고 금지
- 일반 상품은 결제 완료와 `on_hand_committed_qty >= shippable_qty`일 때만 출고
- 차단 승인 작업이 있으면 새 Payment와 예약 만료 해제 금지

## Phase 9+ 모델

쿠폰(`Coupon`, `UserCoupon`, `OrderCoupon`), 알림, CS, 회원 주소 등은 해당 Phase 시작 시 이 문서에 구현 가능한 수준으로 다시 구체화한다.
