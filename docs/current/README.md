# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 있다. Production EC2는 아직 없다. Vercel은 `DJANGO_ORIGIN` 적용 재배포가 Ready이고 인증 경로는 API HTTPS 미연결로 502다. EC2에 Nginx·Docker·Compose·Certbot을 설치하고 ECR pull 권한을 연결했다. API HTTP는 200, HTTPS 443은 아직 연결 거부다.
- [학습 목차](../artifact/index.html)는 전체 시스템, AWS 접속·배포·주소·DNS, 인증·메일 가이드를 연결한다. 각 주제에서 일반적인 대안과 장단점을 먼저 비교하고 TRACEBACK 선택·코드·미검증 상태를 구분한다. SSM 사용자의 `/opt/traceback` 접근 권한도 접속 가이드에 설명했다. GitHub Pages 게시 워크플로는 이 PR에 있고 `github-pages` 환경은 `development` 배포만 허용하므로 병합 뒤 공개 URL을 검증한다.

## Validation / Next action

- 8개 HTML 게시 빌드와 문서 내 이동 링크 검사가 통과했다. PR #12의 Quality·Test는 통과했고 CodeRabbit은 review paused 상태다. AWS 리소스 변경과 실제 배포는 아직 진행하지 않았다.
- Pages URL은 아직 404다. 게시 workflow가 PR 브랜치에만 있고 `github-pages` 환경은 `development`만 허용한다. 병합 뒤 실제 배포와 공개 URL을 검증한다.
- API 인증서 발급과 Nginx 프록시 설정, EC2 `.env`·RDS DB 사용자·Django 이미지 배포가 남았다. HTTP 200과 ACME 검증 경로, Vercel auth 경로 502, ECR 저장소 이미지 0개를 확인했다. 순서는 [2번 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 작업은 [`../todo.md`](../todo.md)에 둔다.
