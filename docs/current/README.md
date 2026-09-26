# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice가 구현되어 있다.
- 현재 브랜치는 `phase-0d-pr8-review-round2`이며 PR #8의 CodeRabbit 지적 5개를 반영했다. 로컬 호스트 DB URL, 외부 Action SHA 고정, 운영 승격 SHA, `detail` 필드 오류, 로컬 DB 포트 바인딩을 수정했다.
- Kakao provider unlink, account deletion, 사용자별 세션 추적이 구현되어 있다.
- 로컬 메일은 console, AWS development/production 메일은 SES SMTP를 사용한다. `.env.example`과 `config/server.env.example`에 SES 인증 변수 이름을 명시했다.
- `development`/`main` push의 quality·test 성공 뒤에만 배포 job이 호출된다. Development는 SHA 이미지가 이미 있으면 재사용하고, production은 성공한 development CI의 SHA로 조회한 동일 digest를 승격한다. EC2는 이미지 속 Compose 파일을 반영하고 migration 후 HTTP/DB healthcheck가 통과한 앱을 실행한다.
- `.env.dev.git`/`.env.prod.git`는 GitHub Environment 변수 목록이고,
  EC2 `/opt/traceback/.env`의 변수 목록은 `config/server.env.example`이다. AWS/GitHub 수동 설정은 `docs/deployment.md`에 정리했다.
- `visualizations/index.html`은 전체 구조·인증·CI/CD·코드 지도의 진입점이다. System Guide는 외부 Action SHA, 앱 커밋 SHA, ECR digest와 현재 구현 파일의 실행 경로를 설명한다.

## Validation

- Backend SQLite suite 40 passed, 96.23% coverage. Ruff, format, mypy, YAML lint, production 배포 단계 셸 구문, local/production Compose config 통과. 로컬 DB 포트가 `127.0.0.1:15432`로 렌더링됨을 확인했다.
- HTML 링크 57개와 스크립트 문법, 브라우저의 탭·상세 설명 동작을 확인했다.
- 수정 브랜치의 원격 CI와 실제 AWS 배포는 미검증. 최근 development CI는 quality/test가 통과했지만 GitHub `development` Environment의 변수 4개가 비어 있어 배포가 `aws-region` 누락으로 실패했다. AWS 리소스는 생성하지 않았다.

## Next action

- 수정 브랜치를 `development`에 PR로 검토·병합한 뒤 원격 CI를 확인한다.
- 소유자가 `docs/todo.md` 순서에 따라 AWS 개발 환경과 GitHub Environment 변수를 준비한다. 설정 후 development 배포/HTTP·DB smoke를 검증한다. Production은 source SHA·digest·migration 영향 확인과 명시적 승인 뒤 배포한다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
