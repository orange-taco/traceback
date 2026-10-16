# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포 가이드와 스크립트가 PR #12에 있다. Production EC2는 아직 없다. Vercel은 `DJANGO_ORIGIN` 적용 재배포가 Ready이고 인증 경로는 API HTTPS 미연결로 502다. EC2에 Nginx·Docker·Compose·Certbot을 설치하고 ECR pull 권한을 연결했다. API HTTP는 200, HTTPS 443은 아직 연결 거부다.
- [학습 목차](https://orange-taco.github.io/traceback-artifacts/)와 작성 스킬은 별도 `orange-taco/traceback-artifacts` 저장소에서 관리한다. iPad는 게시된 사이트에서 읽는다. Codex Cloud의 비공개 `TRACEBACK Study (3 repos)` 환경에 문서·백엔드·프런트 저장소를 연결해 게시했다. 사이트 내 수정 요청 기능은 아직 없다. 백엔드 저장소의 HTML 복사본과 Pages 워크플로는 제거한다.
- [인증 결정 가이드](https://orange-taco.github.io/traceback-artifacts/auth-session-allauth-guide.html#external-unlink)는 Kakao unlink의 부분 실패와 작업 복구 설계를 설명한다. 상태·작업 행과 재시도는 개선 설계로 아직 구현되지 않았다.
- SES 서울 리전에 `dev-traceback.com` 발신 도메인을 등록하고 Easy DKIM 검증을 완료했다. 개발 발신 주소는 `no-reply@dev-traceback.com`이며 전용 SMTP 계정 인증에 성공했다. RDS 관리자 비밀번호를 재설정하고 `traceback_app` 계정의 로그인·테이블 생성 권한을 검증했다. 자격 증명은 로컬 권한 제한 파일에 있고 EC2에는 아직 없다.
- 로컬 카카오 키는 `traceback_dev-TEST` 앱, AWS 개발 서버 키는 `traceback` 앱에서 가져와야 한다. 잘못 준비된 로컬 배포 환경파일의 테스트 앱 키는 제거하고 배포 앱 REST 키·Client Secret으로 교체했다. Admin Key와 배포 callback URI는 아직 설정 전이다.

## Validation / Next action

- 별도 아티팩트 저장소의 8개 HTML 내부 링크 검사와 Pages 배포가 성공했다. 세 저장소 Cloud 환경을 게시했고 온보딩 중 프런트 타입 검사·빌드, 백엔드 테스트 40개, 문서 링크 검사가 통과했다. 새 Cloud 작업에서 저장소 복원은 아직 별도 확인이 필요하다. 기존 백엔드 PR의 Quality·Test는 통과했고 CodeRabbit은 review paused 상태다. SES 도메인과 DKIM DNS를 추가했으며 실제 앱 배포는 아직 진행하지 않았다.
- 다음 작업은 Kakao Admin Key 권한 범위를 선택하고 Let's Encrypt Subscriber Agreement 동의를 확인하는 것이다. HTTP ACME 경로는 외부에서 검증했다. 개인 이메일은 인증서 발급에 필요 없다. 서버 `.env`·인증서는 없고 HTTPS 443은 연결되지 않았다. 이후 배포용 Kakao callback URI, Nginx, 이미지 배포를 진행한다. SES 샌드박스에서는 수신자 인증 또는 발송 권한 확대도 필요하다. 순서는 [2번 배포 가이드](https://orange-taco.github.io/traceback-artifacts/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 작업은 [`../todo.md`](../todo.md)에 둔다.
