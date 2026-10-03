# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 모여 있다. Production EC2는 아직 없다.
- 학습 순서는 [System Guide](../artifact/traceback-system-guide.html)에서, 새 artifact의 필수 작성 기준은 [시각화 스킬](../../.codex/skills/auth-flow-visualizer/SKILL.md)에서 확인한다.

## Validation / Next action

- PR #12 quality/test 통과. `Deploy development`는 pull request 이벤트에서 조건상 skip됨. 기존 CodeRabbit 지적 5건은 반영했고, 새 review 요청은 rate limit 상태다.
- PR #12의 새 checks/review 상태를 확인한 뒤 `development`에 병합한다. 실제 AWS 배포는 아직 미검증이며, 선행 설정은 [2번 첫 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
