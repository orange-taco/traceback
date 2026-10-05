# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 있다. Production EC2는 아직 없다. Vercel은 `DJANGO_ORIGIN` 적용 재배포가 Ready이고 인증 경로는 API HTTPS 미연결로 502다. EC2에 Nginx·Docker·Compose·Certbot을 설치하고 ECR pull 권한을 연결했다. API HTTP는 200, HTTPS 443은 아직 연결 거부다.
- [학습 목차](https://orange-taco.github.io/traceback-artifacts/)와 작성 스킬은 별도 `orange-taco/traceback-artifacts` 저장소에서 관리한다. iPad는 게시된 사이트에서 읽는다. Codex Cloud의 `traceback` 환경 초안에는 문서·백엔드 두 저장소를 선택했으며 게시 전 설정을 마쳐야 한다. 백엔드 저장소의 HTML 복사본과 Pages 워크플로는 제거한다.
- [인증 결정 가이드](https://orange-taco.github.io/traceback-artifacts/auth-session-allauth-guide.html#external-unlink)는 Kakao unlink의 부분 실패와 작업 복구 설계를 설명한다. 상태·작업 행과 재시도는 개선 설계로 아직 구현되지 않았다.

## Validation / Next action

- 별도 아티팩트 저장소의 8개 HTML 내부 링크 검사가 통과했고 Pages 배포 run이 성공했다. 공개 목차 URL은 HTTP 200으로 확인했다. Codex Cloud 환경은 아직 `게시되지 않음` 상태다. 기존 백엔드 PR의 Quality·Test는 통과했고 CodeRabbit은 review paused 상태다. AWS 리소스 변경과 실제 앱 배포는 아직 진행하지 않았다.
- API 인증서 발급과 Nginx 프록시 설정, EC2 `.env`·RDS DB 사용자·Django 이미지 배포가 남았다. HTTP 200과 ACME 검증 경로, Vercel auth 경로 502, ECR 저장소 이미지 0개를 확인했다. 순서는 [2번 배포 가이드](https://orange-taco.github.io/traceback-artifacts/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 작업은 [`../todo.md`](../todo.md)에 둔다.
