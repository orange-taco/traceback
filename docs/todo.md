# TRACEBACK TODO

현재 범위에는 없지만 추후 필요할 수 있는 선택적 backlog만 기록한다. 다음 세션의
필수 작업 목록이 아니며, 완료한 항목과 오래된 작업 이력은 남기지 않는다.
설계 결정은 이 문서가 아니라 [`system.md`](system.md) 또는
[`build-plan.md`](build-plan.md)에 기록한다.

## Optional backlog

- [ ] abandoned account cleanup 정책 결정
  - 대상: 가입 미완료, 인증 정보 없음, SocialAccount 없음, 보존 기간 경과 계정
  - 결정 필요: 보존 기간, 삭제/익명화 범위, Celery 도입 시점
- [ ] Celery/background job과 queue 도입 여부 결정
- [ ] 활성 세션 목록과 전체 기기 로그아웃 UI 검토
- [ ] Phase 9+ coupon, notification, CS, address, preorder 상세 설계

## Maintenance

- backlog 항목은 새 세션마다 처리하지 않는다.
- 해당 영역의 task를 시작할 때만 관련 항목을 읽고, 필요하면 설계 결정으로 승격한다.
- 구현이 확정되면 항목을 삭제하고 `system.md` 또는 `build-plan.md`에 기록한다.
- Phase에 들어간 작업은 `build-plan.md`에서 관리한다.
