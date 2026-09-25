# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice가 구현되어 있다.
- 현재 브랜치는 `phase-0d-pr8-hardening`이며 GitHub-hosted runner + AWS OIDC + SSM 배포 설정을 준비했다. 기존 미커밋 변경은 보존했다.
- Kakao provider unlink, account deletion, 사용자별 세션 추적이 구현되어 있다.
- 로컬 메일은 console, AWS development/production 메일은 SES SMTP를 사용한다. `.env.example`과 `config/server.env.example`에 SES 인증 변수 이름을 명시했다.
- `development`/`main` push의 quality·test 성공 뒤에만 배포 job이 호출된다. Development는 SHA 이미지가 이미 있으면 재사용하고, production은 성공한 development CI의 SHA로 조회한 동일 digest를 승격한다. EC2는 이미지 속 Compose 파일을 반영하고 migration 후 HTTP/DB healthcheck가 통과한 앱을 실행한다.
- `.env.dev.git`/`.env.prod.git`는 GitHub Environment 변수 목록이고,
  EC2 `/opt/traceback/.env`의 변수 목록은 `config/server.env.example`이다. AWS/GitHub 수동 설정은 `docs/deployment.md`에 정리했다.

## Validation

- Backend SQLite suite 39 passed, 96.18% coverage. Ruff, format, mypy, 변경된 workflow/Compose YAML lint, 셸 구문, Compose config, production Docker build 및 실제 production-container migration/HTTP·DB healthcheck 통과.
- 실제 GitHub Actions/OIDC/ECR/SSM 배포와 production HTTP/DB smoke는 미검증. 조회 시 GitHub에는 `local` Environment만 있고, 로컬 AWS 자격 증명의 서울 리전에는 `traceback` ECR 저장소와 SSM 등록 인스턴스가 없었다. 인프라를 생성하거나 실제 배포하지 않았다.

## Next action

- 소유자가 `docs/todo.md`의 Phase 0 순서에 따라 개발 환경부터 준비하고 대상 계정·리전·비용을 확인한다.
- 설정 후 development 배포/HTTP·DB smoke를 검증한다. Production은 source SHA·digest·migration 영향 확인과 명시적 승인 뒤 배포한다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
