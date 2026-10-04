# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 있다. Production EC2는 아직 없다. Vercel은 `DJANGO_ORIGIN` 적용 재배포가 Ready이고 인증 경로는 API HTTPS 미연결로 502다. EC2에 Nginx·Docker·Compose·Certbot을 설치하고 ECR pull 권한을 연결했다. API HTTP는 200, HTTPS 443은 아직 연결 거부다.
- 다섯 가이드는 [학습 목차](../artifact/index.html)에서 한 주소로 연다. 여섯 HTML 문서의 코드·흐름을 2026-10-04 저장소와 공개 경로에 대조해 Compose 포트, 인증 분기, EC2·Vercel 상태 설명을 맞췄다. GitHub Pages는 workflow 방식이고 `github-pages` 환경은 `development` 배포만 허용한다. 게시 워크플로는 이 PR에 있어 병합 뒤 공개 URL을 검증한다.

## Validation / Next action

- Pages URL은 아직 404다. 게시 workflow가 PR 브랜치에만 있고 `github-pages` 환경은 `development`만 허용한다. 게시 브랜치 결정 뒤 실제 배포와 공개 URL을 검증한다.
- API 인증서 발급과 Nginx 프록시 설정, EC2 `.env`·RDS DB 사용자·Django 이미지 배포가 남았다. HTTP 200과 ACME 검증 경로, Vercel auth 경로 502, ECR 저장소 이미지 0개를 확인했다. 순서는 [2번 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 지금 할 일과 이후 작업의 순서 목록은 [`../todo.md`](../todo.md)에서 관리한다.
