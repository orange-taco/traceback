# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice가 구현되어 있다.
- 현재 브랜치는 `phase-0d-pr8-hardening`이며 PR #8 배포 설정을 보강 중이다.
- Kakao provider unlink, account deletion, 사용자별 세션 추적이 구현되어 있다.
- 로컬 메일은 console, AWS development/production 메일은 SES SMTP를 사용한다.

## Validation

- 기존 `development`의 Backend SQLite suite: 39 passed, 96% coverage
- 기존 Ruff, format, mypy, Django check, yamllint, Compose 검증 통과
- 이 브랜치의 rebase 후 검증은 아직 진행하지 않았다.

## Next action

- PR #8 배포 설정과 문서의 남은 CodeRabbit 항목을 하나씩 처리한다.
- 개발/운영 EC2 분리와 ECR 이미지 승격 방식을 구현 전에 확정한다.
- 이후 client QA와 Phase 0 배포 검증을 진행한다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
