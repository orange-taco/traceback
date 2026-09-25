# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice가 구현되어 있다.
- 현재 브랜치는 `phase-0d-pr8-hardening`이며 PR #8 배포 설정을 보강 중이다.
- Kakao provider unlink, account deletion, 사용자별 세션 추적이 구현되어 있다.
- 로컬 메일은 console, AWS development/production 메일은 SES SMTP를 사용한다.
- `development` push는 ECR 이미지를 빌드해 development EC2에 배포하고,
  `main` push는 development에서 성공한 동일 digest를 production EC2에 배포한다.
- `.env.dev.git`/`.env.prod.git`는 GitHub Environment 변수 목록이고,
  EC2 `/opt/traceback/.env`의 변수 목록은 `config/server.env.example`이다.

## Validation

- 최신 `development` 위로 rebase 후 Backend SQLite suite 39 passed,
  96.18% coverage.
- 배포 workflow YAML/셸 구문, 공통 SSM 스크립트 모의 실행,
  CI 운영 smoke 환경파일 Compose 구성 및 diff check 통과.
- 실제 AWS development/production 배포는 아직 검증하지 않았다.

## Next action

- PR #8의 남은 문서 리뷰(브랜치명과 인증 경로)를 처리한다.
- AWS development/production EC2, GitHub Environment, ECR 권한을 준비하고
  실제 배포에서 같은 image digest가 사용되는지 검증한다.
- 이후 실제 배포, SES, client QA를 검증한다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
