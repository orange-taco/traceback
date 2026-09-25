# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice가 구현되어 있다.
- django-allauth Headless email/password와 Kakao OAuth를 사용한다.
- Kakao provider unlink와 account deletion이 구현되어 있다.
- `allauth.usersessions`로 사용자별 세션을 추적·종료한다.
- TRACEBACK 시스템의 큰 구조와 확정 결정은 [`../system.md`](../system.md)에 있다.
- 다음 큰 단계는 client QA와 Phase 0 배포 검증이다.

## Validation

- Backend SQLite suite: 39 passed, 96% coverage
- Ruff, format, mypy, Django check, yamllint, and diff check passed
- Compose production config rendered successfully with PostgreSQL readiness healthcheck
- Local PostgreSQL test validation remains unavailable while the `db` service hostname is not reachable.

## Next action

- PR #9 CodeRabbit re-review 결과를 확인한다.
- 이후 client QA와 Phase 0 배포 검증을 진행한다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다. 이는 새 세션의 필수 작업 목록이 아니다.
- task 종료 시 오래된 현재 작업, 검증, 다음 행동을 실제 코드 상태에 맞게 갱신한다.
- 과거 완료 이력과 긴 검증 로그는 남기지 않는다.
