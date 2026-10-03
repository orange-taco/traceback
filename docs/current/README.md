# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 모여 있다. Production EC2는 아직 없다.
- 학습 순서와 각 artifact의 역할은 [System Guide](../artifact/traceback-system-guide.html)에서 확인한다.

## Validation / Next action

- PR #12의 CI quality/test 통과; `Deploy development`는 pull request 이벤트에서 조건상 skip됨. PR 리뷰의 유효한 지적과 문서 갱신 후 checks를 다시 확인한다.
- 실제 AWS 배포는 아직 미검증이다. 선행 설정 및 NACL 확인은 [2번 첫 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
