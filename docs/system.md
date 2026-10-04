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
- Kakao unlink 성공 후 User·SocialAccount·EmailAddress를 한 DB transaction에서
  정리하고, UserSession 종료는 transaction이 끝난 뒤 실행한다.
- 현재 구현은 원격 Kakao 성공 후 로컬 DB 실패를 복구하는 영속 작업 기록이 없다.
  `validate_disconnect()`에서도 검증 중 원격 unlink를 호출한다. 두 경로의
  상태 전이·작업 점유·재시도 설계는 미구현이며 Phase 0에서 결정·수정한다.
- Kakao `-101`은 이미 unlink된 상태이므로 성공으로 처리한다.
- 사용자 세션은 `allauth.usersessions`로 사용자별 조회·종료한다.
- SocialAccount 연결 해제의 검증·삭제 흐름은 allauth Headless endpoint를 사용한다.
- 계정 전체 삭제는 `/accounts/delete`에서 이메일 전용이면 로컬 DB만 정리하고,
  Kakao 전용·이메일+Kakao이면 provider unlink 후 로컬 DB를 정리한다. User 행은
  soft delete로 남겨 `is_active=False`, `deleted_at` 및 익명화·비밀번호 무효화를
  적용한다. EmailAddress와 SocialAccount 행은 실제 삭제한다.

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
- Local: Docker Compose PostgreSQL, local file storage
- AWS development/production: 별도 EC2와 RDS PostgreSQL을 사용한다. Development
  배포 준비 때 dev RDS와 private S3 버킷을 만든다. Production은 별도 리소스로 나중에
  준비한다. 초기 dev는 계정 Free Tier/credit을 먼저 확인하고, 단일 EC2·Single-AZ
  micro RDS로 시작하며 NAT Gateway·Load Balancer는 두지 않는다. EC2 메모리 여유를
  확인하고 필요할 때만 크기를 올린다.
- DNS/domain: 도메인 등록과 authoritative DNS 관리는 Route 53을 사용한다. Development
  EC2에는 Elastic IP `3.34.78.140`을 연결했고, Route 53 `api.dev-traceback.com` A 레코드가
  이를 가리킨다(TTL 300초). 도메인은 Route 53에 등록되어 ACTIVE이고 hosted zone과 등록
  네임서버가 일치한다. 실행 중 기본 공인 IPv4와 EIP 요금은 같고, EIP는 EC2를 중지해도
  시간당 요금이 계속 발생한다. 주소가 유지되므로 동적 DNS 갱신 자동화는 필요 없다.
  Production DNS는 별도 환경 준비 때 정한다.
- Frontend: Vercel에서 React Router SSR을 운영한다. Django API는 Vercel과 분리해 각 환경의 AWS EC2에서 운영하며, 프런트 전용 EC2는 만들지 않는다. 브라우저 same-origin 세션 계약을 유지하도록 Vercel에서 `/_allauth`, `/accounts`, API 경로를 해당 환경의 EC2로 전달한다. Kakao OAuth callback까지 실제 배포에서 검증한다.
- Object storage: S3는 업로드 파일 저장용으로 사용한다. Development 버킷은 배포 준비에
  포함하며 public access를 차단한다. 실제 앱 업로드 연동과 최소 IAM 권한은 이미지 업로드
  기능 구현 때 추가한다. 현재 프런트 SSR을 CloudFront/S3 정적 사이트로 바꾸지 않는다.
- App: Gunicorn + Uvicorn worker + Django ASGI
- Compose: `docker-compose.yml` is the local development stack (runserver, source mount, Docker PostgreSQL). `docker-compose_prod.yml` is the immutable-image server runtime overlay shared by development and production EC2; the server `.env` selects `config.settings.development` or `config.settings.production`. A separate `docker-compose_dev.yml` is not needed for the confirmed shared EC2 runtime.
- Runtime: GitHub Actions가 `development` 커밋의 production image를 한 번 빌드해 ECR에 저장한다. Development EC2에서 검증한 동일 image digest를 `main` 배포 때 production EC2가 실행한다.
- CI/CD: GitHub-hosted runner만 사용하며 `quality`와 `test`가 성공한 push에서만 환경별 CD를 호출한다. GitHub Actions는 OIDC로 환경별 제한된 AWS IAM Role을 인수하고, SSM으로 각 환경의 EC2에 배포한다. 장기 AWS Access Key는 GitHub에 저장하지 않는다.
- 환경 분리: GitHub Environment는 development/production으로 나누고 앱 EC2·DB도 별도로 둔다. 앱 EC2는 SSM 관리 권한과 지정 ECR image pull 권한만 받는다. Production은 development에서 배포 성공한 동일 image digest만 승격하며 새로 빌드하지 않는다.
- Migration: CI는 임시 DB에서 검증하고, 실제 환경의 `migrate --noinput`은 CD에서 새 애플리케이션 실행 전에 수행한다.
- Branch flow: feature → `development` → `main`. Release PRs use a merge commit;
  production promotes the image for its development parent commit.
- Secrets: 현재 각 EC2의 `/opt/traceback/.env`에 런타임 비밀값을 보관한다. Secrets Manager 전환은 별도 결정이다. Repository에는 placeholder만 둔다.
- GitHub Environment 변수 목록은 `.env.dev.git`/`.env.prod.git`에, EC2 런타임 변수 목록은 `config/server.env.example`에 둔다. 각 서버의 비밀값은 추적하지 않는 `/opt/traceback/.env`에 넣고 Compose가 app 컨테이너에 전달한다.
- AWS/GitHub 수동 설정과 배포 검증 절차는 [`deployment.md`](deployment.md)를 따른다.
- 학습용 HTML은 `docs/artifact/`를 GitHub Pages에 공개한다. `development`에서
  목차와 문서·이미지만 게시하고, 저장소 코드 링크는 GitHub 원문으로 연결한다.
  메모·댓글 저장 기능은 별도 결정 전까지 두지 않는다.
- Local email은 console mailer로 출력하고, AWS 환경은 SES SMTP(STARTTLS, 587)를 사용한다.

## Deferred

- Celery/background job과 queue는 비동기 작업이 실제로 필요할 때 도입한다.
- abandoned account cleanup은 가입 완료 상태·보존 기간·정리 범위를 먼저 확정한 뒤 추가한다.
- Coupon, notification, CS, address, preorder 상세는 해당 Phase에서 결정한다.
- AWS network, ECR lifecycle, secret rotation, APM 상세는 AWS development 첫 배포 전 확정한다. S3는 development 버킷을 배포 준비에 만들고, production 버킷은 production 환경 구축 때 준비한다. Vercel 프로젝트·도메인·환경별 백엔드 경로 연결은 [`todo.md`](todo.md)와 [`deployment.md`](deployment.md)의 프런트 배포 항목을 따른다.
