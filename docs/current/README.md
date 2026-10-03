# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 서버 배포 준비와 초보자용 학습 문서를 정리하고 있다. 개발 환경만 실제 배포 대상으로 삼으며 production 리소스는 아직 만들지 않는다.
- 배포 설정/코드 문서는 PR #12 브랜치 `phase-0-development-deployment`에, AWS 학습 문서 1·3·4번은 PR #13 브랜치 `docs/aws-deployment-learning`에 분리되어 있다. PR이 나뉜 것은 변경을 두 묶음으로 나눴기 때문이며, 네 학습 문서는 그대로 유지한다.
- 읽기 순서: [1. SSH와 SSM](../artifact/1-aws-ssm-ssh-learning-guide.html) → [2. 첫 서버 배포와 전체 설정](../artifact/2-dev-server-first-deployment.html) → [3. 개발 서버 IP와 도메인](../artifact/3-development-ip-domain-guide.html) → [4. DNS 동작과 관리](../artifact/4-dns-resolution-map.html).
- [CI/CD 시스템 가이드](../artifact/traceback-system-guide.html)는 네 편의 학습 순서와 별도로, 세 workflow와 배포 스크립트 원문을 자세히 읽는 보충 자료다.
- 현재 EC2·RDS·EIP·Route 53과 GitHub OIDC 설정을 준비했다. 실제 배포 전 EC2 ECR pull 권한, Docker/Compose/AWS CLI 설치, RDS 앱 계정, `/opt/traceback/.env`, Nginx/TLS가 남아 있다. Vercel의 `DJANGO_ORIGIN`은 HTTPS API 준비 뒤 등록한다.

## Validation

- 두 작업 브랜치의 CI/CD 원격 검증 및 실제 AWS 배포는 아직 완료되지 않았다.
- 이번 문서 정리에서는 내부 링크, HTML 구조, 삽입된 코드 원문, 스크립트 구문과 `git diff --check`를 확인한다.

## Next action

- 네 학습 문서의 파일명·교차 링크를 읽기 순서에 맞추고, CI/CD 시스템 가이드와 역할이 겹치지 않게 정리한다.
- 준비 체크리스트를 완료한 뒤 development 실배포와 브라우저 기반 HTTP·로그인·DB smoke를 진행한다. Production 배포는 범위 밖이다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
