# Account Model Purpose

이 문서는 현재 migration 기준 account/auth 모델과 각 컬럼의 목적을 요약한다.

## User

| Column | Purpose |
| --- | --- |
| `email` | 로그인과 계정 식별에 사용하는 unique 대표 이메일 |
| `username` | 고객 노출이 가능한 unique 사용자명; 가입 시 임의 값 생성 |
| `username_changed_at` | 사용자명 변경 제한과 운영 추적 기준 |
| `name` | 선택적인 실명 또는 표시 이름 |
| `phone_e164` | SMS 인증 후 저장하는 정규화 전화번호 |
| `phone_verified_at` | 전화번호 소유 확인 시각; welcome benefit 중복 기준 |
| `is_active` | 로그인 가능 여부 |
| `is_staff` | staff API 접근 기준 |
| `is_superuser` | Django 권한 시스템의 전체 권한 플래그 |
| `deleted_at` | 탈퇴·익명화 정책을 적용할 논리 삭제 시각 |
| `last_login` | Django 인증의 최근 로그인 시각 |
| `password` | Django password hasher 결과; 원문은 저장하지 않음 |
| `created_at`, `updated_at` | 가입 시각과 레코드 변경 추적 |

활성 인증 전화번호는 DB partial unique constraint로 중복을 막는다.

## BenefitClaim

| Column | Purpose |
| --- | --- |
| `code` | 지급한 혜택 종류 |
| `user_id` | 혜택 수령 User; 탈퇴 후 참조 해제를 위해 nullable |
| `phone_hash` | 원문 전화번호 대신 저장하는 HMAC hash |
| `claimed_at` | 혜택 지급 시각 |
| `claim_source` | 지급을 발생시킨 흐름 |
| `metadata` | 감사에 필요한 비정형 부가 정보 |

`welcome_signup`은 `phone_hash`가 필수이며 같은 hash에는 한 번만 지급된다.

## Framework-Owned Auth Models

| Model | Purpose |
| --- | --- |
| `account.EmailAddress` | User 이메일의 primary/verified 상태와 인증 흐름 |
| `socialaccount.SocialAccount` | provider와 provider UID를 User에 연결하고 provider 응답 보관 |
| `sessions.Session` | 서버 측 인증 상태; browser에는 HttpOnly session ID만 전달 |

기존 `accounts.SocialAccount`, `EmailChangeRequest`, `UserToken`,
`User.email_verified_at`은 allauth 모델과 중복되므로
`accounts.0004_move_auth_state_to_allauth`에서 데이터를 이전한 뒤 제거한다.
