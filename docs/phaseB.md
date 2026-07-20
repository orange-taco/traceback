# Phase 0B Account/Auth Decisions

이 문서는 Phase 0B common API/auth 작업에서 확정한 계정, 인증,
소셜 로그인, 혜택 중복 방지 결정을 기록한다.

## Scope

Phase 0B는 커머스 도메인 기능을 만들지 않고, 이후 Catalog/Cart/Order가
의존할 계정과 공통 인증 기반만 만든다.

## User Model

- Custom User를 사용한다.
- Django `AbstractBaseUser` + `PermissionsMixin` 기반으로 설계한다.
- 로그인 식별자는 email이다.
- `USERNAME_FIELD = "email"`로 둔다.
- email은 저장, 가입, 로그인, 이메일 변경, 소셜 자동 연결 전에 동일한 규칙으로 정규화한다.
- 정규화 규칙은 앞뒤 공백 제거 후 전체 주소를 소문자로 변환하는 것이다.
- email unique 검증과 로그인 lookup은 정규화된 email 기준으로 수행한다.
- 로그인 lookup과 소셜 자동 연결 대상은 `is_active = true`이고 `deleted_at is null`인 User로 제한한다.
- `username`은 로그인 ID가 아니라 화면 표시용 닉네임/핸들로 사용한다.
- `username`은 자동 생성하고 unique로 둔다.
- `nickname` 필드는 만들지 않는다.
- 단일 브랜드 커머스이므로 일반 seller/merchant/vendor 권한은 만들지 않는다.
- 관리자 권한은 Django의 `is_staff`, `is_superuser`, group/permission 기반을 사용한다.

필드 방향:

```text
User
- id
- email unique required, normalized
- username unique required, auto-generated
- username_changed_at nullable
- name nullable
- phone_e164 nullable
- phone_verified_at nullable
- email_verified_at nullable
- is_active
- is_staff
- is_superuser
- deleted_at nullable
- last_login
- joined_at
- created_at
- updated_at
```

## Email Signup And Login

- 이메일 + 비밀번호 회원가입을 지원한다.
- 가입 직후 로그인과 구매를 허용한다.
- 이메일 미인증이어도 구매 가능하다.
- 비회원 구매도 허용한다.
- `name`은 회원가입 때 필수로 받지 않는다.
- `name`은 주문 시 입력받고, 회원은 마이페이지에서도 설정할 수 있다.
- 가입 후 이메일 인증 메일은 보낼 수 있지만, 인증 전 구매를 막지 않는다.
- 비밀번호 정책은 Django 기본 password validators를 사용한다.

## Social Login

- 초기 provider는 `kakao`, `naver`만 지원한다.
- Apple은 초기 범위에서 제외한다.
- Google도 초기 범위에서 제외한다.
- 소셜 가입 사용자는 password를 unusable로 시작할 수 있다.
- 소셜 가입자가 이메일/password 로그인을 추가하려면 이메일 링크 기반 password 설정을 거친다.

모델:

```text
SocialAccount
- id
- user FK
- provider
- provider_user_id
- provider_email nullable
- provider_email_verified
- is_active
- linked_at
- deleted_at nullable
- created_at
- updated_at
```

제약:

```text
unique(provider, provider_user_id)
unique(user, provider)
```

`provider_email`은 서비스 대표 이메일이 아니라 provider가 로그인 시점에 준
이메일 snapshot이다. 자동 연결 판단과 감사/디버깅 근거로 사용한다.
소셜 로그인 lookup은 `is_active = true`이고 `deleted_at is null`인 `SocialAccount`만 대상으로 한다.
회원 탈퇴 시 `SocialAccount`는 삭제하지 않고 비활성화한다.
탈퇴 처리에서는 `is_active = false`, `deleted_at = now`로 두고,
`provider_user_id`는 `deleted:{social_account_id}` 형태로 익명화해 unique slot을 해제한다.
`provider_email`은 null로 지우고 `provider_email_verified = false`로 변경한다.
탈퇴 후 같은 provider 계정으로 재가입하면 기존 비활성 `SocialAccount`를 재사용하지 않고 새 행을 만든다.

## Social And Email Account Linking

공통 전제:

- `User.email`은 정규화된 서비스 대표 이메일이며 unique/required이다.
- 이메일 기반 가입, 로그인, 자동 연결 lookup은 활성·비삭제 User만 대상으로 한다.
- 탈퇴한 User는 email을 익명화하므로 같은 원문 이메일로 재가입할 수 있다.
- `SocialAccount.provider_email`은 provider email snapshot이다.
- `provider + provider_user_id`가 소셜 계정의 1차 식별자다.

### Social First, Then Email

소셜로 먼저 가입한 뒤 같은 이메일로 email/password 가입을 시도하는 경우:

- 새 User를 만들지 않는다.
- 기존 User가 있으므로 이미 가입된 이메일로 처리한다.
- password가 없으면 이메일 링크 기반 password 설정 플로우로 안내한다.
- password 설정 후 같은 User로 email/password 로그인을 허용한다.

### Email First, Then Social

email/password로 먼저 가입한 뒤 같은 이메일의 소셜 로그인을 시도하는 경우:

- 기존 `User.email_verified_at`이 있고 provider email도 verified이면 같은 User에
  `SocialAccount`를 자동 연결한다.
- 기존 `User.email_verified_at`이 없으면 자동 연결하지 않는다.
- 미인증 이메일 계정에 소셜을 자동 연결하면 account pre-hijacking 위험이 있다.
- 이 경우 기존 계정으로 로그인 후 이메일 인증 또는 명시적 소셜 연결을 하도록 안내한다.

## Email Change

- 대표 이메일 변경을 허용한다.
- 새 이메일 인증이 완료되기 전까지 기존 `User.email`을 유지한다.
- 이메일 변경은 별도 `EmailChangeRequest` 모델로 관리한다.
- 이메일 변경 요청은 24시간 뒤 만료한다.
- 재요청은 같은 user 기준 10분에 1회 허용한다.
- 새 요청이 생성되면 기존 미확정 요청은 만료 처리한다.

모델:

```text
EmailChangeRequest
- id
- user FK
- new_email
- token_hash
- expires_at
- confirmed_at nullable
- created_at
```

규칙:

- `new_email`은 요청 시점과 확정 시점 모두 unique를 검사한다.
- token 원문은 저장하지 않고 hash만 저장한다.
- 미확정 활성 요청은 user당 1개만 유지하거나 새 요청 시 기존 요청을 만료한다.

## User Token

`EmailChangeRequest`는 확정된 설계다.

`UserToken`은 이를 대체하는 모델이 아니라, 이메일 변경 외의 단순 토큰 작업을
공통화하는 모델이다.

용도:

- 회원가입 이메일 인증
- 소셜 가입자의 password set
- email/password 사용자의 password reset

모델:

```text
UserToken
- id
- user FK
- purpose: email_verify/password_set/password_reset
- token_hash
- expires_at
- consumed_at nullable
- created_at
```

검토 이유:

- 회원가입 이메일 인증, password set, password reset은 모두 같은 형태의
  user-bound one-time token이다.
- 반면 이메일 변경은 `new_email`이 필요하므로 `EmailChangeRequest`가 더 명확하다.

만료 시간:

```text
email_verify: 24시간
password_set: 1시간
password_reset: 1시간
```

실제 token 발급/소비 API와 이메일 발송, 클라이언트 연동 flow는
회원가입/로그인 클라이언트 구현 시점에 구현한다.

## Phone Verification

- 가입 시 phone은 받지 않는다.
- SMS 인증 시점에 사용자가 phone을 입력한다.
- SMS 인증 성공 후 `User.phone_e164`와 `User.phone_verified_at`을 저장한다.
- 인증된 phone은 활성 User 하나에만 연결되도록 강제한다.
- 탈퇴한 User의 phone은 제거하므로 같은 번호로 재가입 계정에서 다시 인증할 수 있다.

PostgreSQL partial unique index 방향:

```text
unique(phone_e164)
where phone_verified_at is not null and deleted_at is null
```

## Welcome Benefit / Coupon Abuse Prevention

- 웰컴 쿠폰은 회원가입 즉시 자동 지급하지 않는다.
- 웰컴 쿠폰은 phone SMS 인증 완료 후 지급한다.
- 계정 생성 경로가 email/password, kakao, naver 중 무엇이든 phone 기준으로 1회만 지급한다.
- 이메일이나 소셜 계정 연결은 계정 편의성 문제이고, 혜택 중복 방지는 phone hash ledger로 분리한다.
- `BenefitClaim`은 중복 혜택 지급 방지 ledger로 장기 보관한다.
- 원문 phone/email/social identity는 저장하지 않고 서버 secret pepper 기반 HMAC hash만 저장한다.
- 개인정보 처리방침에는 부정 이용 및 중복 혜택 지급 방지를 위해 일부 식별정보를 복호화할 수 없는 방식으로 변환하여 보관할 수 있음을 반영한다.

모델명:

```text
BenefitClaim
```

필드:

```text
BenefitClaim
- id
- code
- user nullable
- phone_hash nullable, required when code = "welcome_signup"
- claimed_at
- claim_source
- metadata
```

MVP 정책:

```text
code = "welcome_signup"
phone_hash is not null
unique(code, phone_hash)
```

실제 혜택 지급 API와 클라이언트 연동 flow는 회원가입 클라이언트 구현 시점에 구현한다.

Hash 정책:

- 원문 phone을 혜택 ledger에 저장하지 않는다.
- 서버 secret pepper를 사용한 phone HMAC hash를 저장한다.
- 탈퇴 후에도 `BenefitClaim`은 중복 지급 방지 목적의 HMAC hash ledger로 장기 보관한다.

## Deactivation / Withdrawal

- 회원 탈퇴는 hard delete가 아니라 soft delete + anonymization으로 처리한다.
- 탈퇴 후 같은 이메일/전화번호 재가입은 허용한다.
- 웰컴 쿠폰 재지급은 `BenefitClaim.phone_hash`로 차단한다.
- `SocialAccount`는 삭제하지 않고 비활성화/익명화하여 보존한다.

탈퇴 처리 방향:

```text
User.is_active = false
User.deleted_at = now
User.email = deleted:{user_id}@deleted.local
User.phone_e164 = null
User.name = ""
User.username = deleted_{user_id}
User.password = unusable
SocialAccount 비활성화/익명화
```

## Username Policy

- `username`은 회원가입 시 자동 생성한다.
- 초기 형식은 `user_{random8}` 계열로 둔다.
- 사용자는 마이페이지에서 변경할 수 있다.
- 변경은 30일에 1회로 제한한다.
- 변경 제한은 `User.username_changed_at`으로 검증한다.
- 최초 자동 생성 시점에는 `username_changed_at`을 null로 둘 수 있고, 사용자가 직접 변경한 시점에 값을 기록한다.
- `username`은 unique이다.

## Deferred From Phase 0B

다음 항목은 Phase 0B에서 구현하지 않는다.

### SiteSetting

- Phase 0B에서는 `SiteSetting`을 만들지 않는다.
- 배송비 계산, 고객 노출 설정, 약관/정책 노출 요구가 명확해지는 Phase에서 다시 확정한다.
- Phase 1 Catalog 또는 Phase 3 Order 시작 전 필요한 필드와 노출 API를 재검토한다.

### IdempotencyRecord

- Phase 0B에서는 `IdempotencyRecord`를 만들지 않는다.
- `POST /orders`, 결제 confirm, webhook, 관리자 재고 조정처럼 실제 멱등 명령 API가
  시작되는 Phase에서 scope/key/request hash/status 계약과 함께 구현한다.
- Phase 3 Order 시작 전에는 반드시 다시 결정한다.

## Resolved Phase 0B Decisions

Phase 0B 구현 전 남아 있던 결정은 2026-07-11에 다음으로 확정했다.

1. `BenefitClaim`은 HMAC hash ledger로 장기 보관하고 원문 개인정보는 저장하지 않는다.
2. `UserToken` 만료 시간은 `email_verify` 24시간, `password_set` 1시간, `password_reset` 1시간으로 둔다.
3. `EmailChangeRequest`는 24시간 뒤 만료하고, 같은 user 기준 10분에 1회 요청을 허용한다.
