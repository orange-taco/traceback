# Traceback Order Flow

> 현재 범위는 [`build-plan.md`](./build-plan.md)를 따른다. 이 문서는 상태 계산, 트랜잭션 경계, 동시성, 재고 흐름의 기준이다.

## 상태 계산

`Order`, `OrderLine`에는 단일 전체 상태를 저장하지 않는다.

`order_status` 우선순위:

1. 모든 라인 전량 취소: `cancelled`
2. 모든 출고 대상 전량 반품: `returned`
3. 일부 반품: `partially_returned`
4. 전량 배송 완료: `delivered`
5. 전량 출고 완료: `shipped`
6. 일부 출고 완료: `partially_shipped`
7. 준비 중 배정 존재: `preparing`
8. 결제 상태가 paid/partially_refunded: `paid`
9. `expired_at` 존재: `expired`
10. 그 외: `pending`

`payment_status`:

- `cancelled`: 승인액 없는 결제 전 전량 취소 또는 0원 주문 internal void
- `processing`: 성공 pay/capture 없이 차단 승인 작업 존재
- `pending`: 성공 승인과 차단 승인 작업 없음
- `paid`: 승인액이 주문 총액이고 완료 환불 없음. 0원은 internal/free pay 필요
- `partially_refunded`: `0 < 완료 환불액 < 승인액`
- `refunded`: 승인액이 있고 완료 환불액과 같음

차단 승인 작업은 pending/processing/waiting-for-deposit authorize/pay/capture 또는 아직 종결되지 않은 성공 authorize다.

`fulfillment_status`: `unfulfilled`, `preparing`, `partially_shipped`, `shipped`, `delivered`.

## 주문 생성

하나의 DB 트랜잭션에서:

1. 요청, 상품 활성 상태, 가격, 배송비, 쿠폰 활성 여부를 검증한다.
2. 대상 Variant를 결정적 순서로 잠그고 구매 가능 수량을 재검증한다.
3. Order, snapshot, OrderLine을 만들고 할인액을 결정적으로 배분한다.
4. 유료 주문은 최초 Payment와 token hash를 만든다.
5. 일반 상품 `reserved_qty`를 증가시키고 라인별 reserve movement를 기록한다.
6. 장바구니 전체 전환이면 Cart를 ordered로 변경한다.

어느 단계든 실패하면 전체 rollback한다.

0원 주문은 같은 트랜잭션에서 internal/free 성공 pay를 만들고 일반 결제 성공 흐름과 동일하게 재고를 확정한다.

## 결제 승인

외부 PG 호출은 DB 트랜잭션 밖에서 수행한다.

1. 짧은 트랜잭션에서 Order/Payment를 잠그고 금액, token, 만료, 처리 가능 여부를 검증한다.
2. 서버 작업 키가 있는 `PaymentTransaction(processing)`을 만들고 커밋한다.
3. 같은 작업 키를 PG idempotency key로 사용해 승인 요청한다.
4. 응답 후 새 트랜잭션에서 Order와 Variant를 잠근다.
5. 성공 transaction을 반영하고 재고 확정 이동을 정확히 한 번 적용한다.

일반 상품 결제 성공:

- `stock_qty -= 수량`
- `reserved_qty -= 수량`
- `on_hand -수량`, `reserved -수량` movement를 같은 correlation ID로 기록

confirm, webhook, polling은 같은 결제 조정 service를 사용한다. 결과가 불명확하면 실패로 단정하거나 새 승인을 만들지 않고 조회/웹훅으로 조정한다.

## 결제 실패 / 재시도 / 만료

- 확정 실패 transaction은 감사 이력으로 보존하고 예약을 즉시 해제하지 않는다.
- 예약 유효 시간 안이고 성공 승인/차단 승인 작업이 없을 때만 새 Payment를 만든다.
- 새 Payment는 기존 주문 총액을 사용하며 상품/금액을 다시 계산하지 않는다.
- 만료 작업은 Order와 Variant를 잠그고 성공/차단 승인 작업이 없는지 재검증한다.
- PG 대기형 결제는 PG에서 expired/cancelled가 확인된 뒤 예약을 해제한다.
- 예약 해제 후 `expired_at`을 기록한다.

예약 만료 후 성공 이벤트의 최소 안전 규칙:

- 신규 승인은 거절한다.
- 이미 발생한 성공은 원문을 기록하고 재고 확정 가능 여부를 잠금 안에서 판단한다.
- 안전하게 확정할 수 없으면 inventory reconciliation hold를 만들고 출고를 차단한다.
- 자동 재확보/보상 환불 범위는 Phase 4 시작 전에 확정한다.

## 취소 / 환불

결제 전 취소:

- Order와 Variant를 잠근다.
- 라인의 reserved 잔액만 해제하고 release movement를 기록한다.
- `cancelled_qty`를 반영한다.
- 명시적 취소에는 `expired_at`을 기록하지 않는다.

결제 후 취소:

1. Order/OrderLine/Fulfillment를 잠그고 취소 가능 수량과 금액을 확정한다.
2. pending/preparing 배정을 해제하고 payment reconciliation hold를 만든다.
3. Refund/RefundLine과 연결된 단일 PaymentTransaction을 PG 호출 전에 커밋한다.
4. PG 성공 후 새 트랜잭션에서 Refund 완료, `cancelled_qty`, 재고 복구를 함께 반영한다.
5. 결과가 불명확하거나 재시도 대기면 수량/재고를 바꾸지 않고 hold와 수량 선점을 유지한다.
6. 완료 또는 PG 미발생 확인 후 rejected 종결 시에만 hold를 해제한다.

0원 주문 취소는 internal void를 기록한다.

## 출고

FulfillmentLine 생성 시 OrderLine을 잠그고 다음을 같은 잠금 구간에서 검증한다.

- 계산 결제 상태가 paid/partially_refunded
- 활성 hold와 진행 중 취소/환불 없음
- 활성 FulfillmentLine 합계가 `shippable_qty` 이하
- 일반 상품 `on_hand_committed_qty >= shippable_qty`

pending/preparing Fulfillment는 취소할 수 있다. shipped/delivered는 되돌리지 않고 반품으로 처리한다.

## 반품

1. 배송 완료 수량에서 진행 중/완료 반품 수량을 뺀 범위 안에서 접수한다.
2. 검수 전에는 `returned_qty`와 재고를 변경하지 않는다.
3. received 상태에서 완료하며 accepted/restock 수량을 검증한다.
4. `returned_qty`는 accepted 수량만큼 증가시킨다.
5. 재판매 가능한 restock 수량만 on-hand 복구 movement를 기록한다.
6. 환불은 완료된 ReturnLine을 근거로 별도 실행한다.

## 멱등성과 동시성

- 고객 명령: `IdempotencyRecord(scope, key)`
- PG 작업: `PaymentTransaction(provider, transaction_type, idempotency_key)`
- 웹훅: `PaymentEvent(provider, event_id)`
- 재고 이동: `InventoryMovement(operation_key)`

잠금 대상:

- 주문 생성/재고 조정: Variant
- 결제/만료/취소: Order, Payment, 관련 Variant
- 출고/반품/환불: OrderLine과 관련 원천 행

잠금은 ID 오름차순 등 결정적 순서로 획득한다.

## Phase 9+

쿠폰과 프리오더 상세 흐름은 해당 Phase 시작 시 추가한다. 구현 전에는 주문 생성과 출고에서 명시적으로 거절한다.
