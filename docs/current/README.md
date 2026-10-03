# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 모여 있다. 가이드는 설정 선행 순서와 미완료 구간을 표시한다. Production EC2는 아직 없다. Vercel Production 범위의 `DJANGO_ORIGIN`은 저장됐지만 API HTTPS·프런트 재배포·인증 검증이 남았다.
- 학습 순서는 [System Guide](../artifact/traceback-system-guide.html)에서, 새 artifact의 필수 작성 기준은 [시각화 스킬](../../.codex/skills/auth-flow-visualizer/SKILL.md)에서 확인한다.

## Validation / Next action

- 다섯 HTML artifact의 링크·이미지·앵커·PDF 버튼·인라인 JS 구문과 시각화 스킬 검증 통과. 최신 원격 CI 결과는 PR #12의 checks에서 확인한다. `Deploy development`는 pull request 이벤트에서 조건상 skip된다.
- PR #12의 새 checks/review 상태를 확인한 뒤 `development`에 병합한다. 실제 AWS 배포는 아직 미검증이며, 선행 설정은 [2번 첫 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 지금 할 일과 이후 작업의 순서 목록은 [`../todo.md`](../todo.md)에서 관리한다.
