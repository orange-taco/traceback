# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 서버 배포 준비와 초보자용 학습 문서를 정리하고 있다. 실제 배포 대상은 development이며 production 인프라는 아직 만들지 않는다.
- 현재 작업 브랜치 `phase-0-development-deployment`에 배포 스크립트와 네 편의 번호가 붙은 AWS 학습 문서가 함께 있다.
- 읽기 순서: [1. SSH와 SSM](../artifact/1-aws-ssm-ssh-learning-guide.html) → [2. 첫 서버 배포와 전체 설정](../artifact/2-dev-server-first-deployment.html) → [3. 개발 서버 IP와 도메인](../artifact/3-development-ip-domain-guide.html) → [4. DNS 동작과 관리](../artifact/4-dns-resolution-map.html).
- [CI/CD 시스템 가이드](../artifact/traceback-system-guide.html)는 네 편의 학습 순서에 연결되는 보충 자료로, 세 workflow 전체 YAML과 배포 스크립트 원문을 설명한다.
- 실제 배포 전 EC2 ECR pull 권한, Docker/Compose/AWS CLI 설치, RDS 앱 계정, `/opt/traceback/.env`, Nginx/TLS가 남아 있다. Vercel의 `DJANGO_ORIGIN`은 HTTPS API 준비 뒤 등록한다.

## Validation

- Quality/Test와 문서 브랜치 검증은 통과했다. 통합 후 파일 링크와 셸 구문을 다시 확인한다.
- 실제 AWS 배포는 아직 검증하지 않았다. 남은 인프라 준비 항목은 2번 문서의 체크리스트에 기록한다.

## Next action

- 통합 브랜치에서 4개 문서, 내부 링크, 코드 원문과 체크포인트를 확인한 뒤 PR을 검토·병합한다.
- AWS 선행 설정을 마치고 development 실배포와 HTTP·로그인·DB smoke를 진행한다. Production 배포는 범위 밖이다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
