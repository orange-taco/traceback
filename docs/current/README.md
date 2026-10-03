# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 있다. Production EC2는 아직 없다. Vercel은 `DJANGO_ORIGIN` 적용 재배포가 Ready이고 인증 경로는 API HTTPS 미연결로 502다.
- 다섯 가이드는 [학습 목차](../artifact/index.html)에서 한 주소로 연다. GitHub Pages는 workflow 방식으로 활성화했고 `github-pages` 환경은 `development` 배포만 허용한다. 게시 워크플로는 이 PR에 있어 병합 뒤 공개 URL을 검증한다.

## Validation / Next action

- Pages 패키지의 로컬 링크·이미지와 workflow 문법을 검증한다. Vercel 재배포 Ready·인증 경로 502 확인. PR의 새 CI와 CodeRabbit 결과는 푸시 후 확인한다.
- PR #12를 `development`에 병합하면 Pages 게시와 개발 배포를 확인한다. AWS API HTTPS·Nginx·Django는 아직 미완료이며 순서는 [2번 배포 가이드](../artifact/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 지금 할 일과 이후 작업의 순서 목록은 [`../todo.md`](../todo.md)에서 관리한다.
