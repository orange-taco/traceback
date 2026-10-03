# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 모여 있다. 가이드는 설정 선행 순서와 미완료 구간을 표시한다. Production EC2는 아직 없다. Vercel Production 범위의 `DJANGO_ORIGIN`은 저장됐지만 API HTTPS·프런트 재배포·인증 검증이 남았다.
- 학습 순서는 [System Guide](../artifact/traceback-system-guide.html)에서, 새 artifact의 필수 작성 기준은 [시각화 스킬](../../.codex/skills/auth-flow-visualizer/SKILL.md)에서 확인한다. 다섯 가이드는 일반 원리 그림 → TRACEBACK 적용 → 펼치는 상세 설명 순서로 읽을 수 있으며, 1번은 SSM 접속의 공통 조건과 로컬 전용 단축 명령을 구분한다.

## Validation / Next action

- 다섯 HTML artifact의 로컬 링크·이미지·앵커·PDF 버튼·details 구조·인라인 JS 구문 검증 통과. 로컬 HTML 브라우저 시각 검사는 이 세션의 브라우저 접근 제한으로 미실시. 최신 원격 CI 결과는 PR #12의 checks에서 확인한다. `Deploy development`는 pull request 이벤트에서 조건상 skip된다.
- PR #12의 새 checks/review 상태를 확인한 뒤 `development`에 병합한다. 실제 AWS 배포는 아직 미검증이며, 선행 설정은 [2번 첫 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 지금 할 일과 이후 작업의 순서 목록은 [`../todo.md`](../todo.md)에서 관리한다.
