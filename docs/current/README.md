# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice와 development 배포 파이프라인이 구현되어 있다.
- 현재 작업 브랜치는 `phase-0-development-deployment`이며 PR #12의 배포 문서·스크립트 보완 작업 중이다. `.github/scripts/deploy-development.sh`와 `deploy-prod.sh`는 환경별 진입점이고, 실제 공통 배포 로직은 `deploy-common.sh`에 둔다.
- GitHub Actions는 개발 이미지 게시 후 SSM으로 development EC2에 배포하며, production은 development에서 검증된 동일 이미지 digest를 승격한다.
- 네 개의 AWS 학습 아티팩트는 순서대로 읽도록 번호를 붙인다. 현재 이 PR에는 2번 첫 배포 가이드와 전체 CI/CD 코드 가이드가 포함된다. 나머지 1·3·4번은 PR #13에서 관리한다.
- AWS 개발 리소스는 준비됐지만 첫 실제 배포에 필요한 EC2 bootstrap, 인스턴스 ECR pull 권한, 앱 DB 계정, `/opt/traceback/.env`, Nginx/TLS가 남아 있다. Vercel의 `DJANGO_ORIGIN`도 HTTPS API가 준비된 뒤 등록해야 한다.

## Validation

- Backend suite와 CI 설정은 이전 작업에서 검증됐다. 현재 배포 스크립트 변경은 shell 문법, YAML, Compose 설정, HTML 링크 및 아티팩트에 삽입한 코드 원문 일치 여부를 검증해야 한다.
- 실제 AWS 배포는 아직 검증하지 않았다. 인프라의 남은 준비 항목은 2번 가이드의 체크리스트에 기록한다.

## Next action

- 4개 AWS 학습 아티팩트의 번호와 링크를 맞추고, 각 문서에 필요한 전체 스크립트/YAML 원문 및 쉬운 설명이 있는지 검증한다.
- 브랜치 PR을 검토·병합한 뒤 AWS 선행 설정을 완료하고 development 실배포와 HTTP·DB smoke를 검증한다. Production은 아직 대상이 아니다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
