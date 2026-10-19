# Current Work

새 세션은 이 요약과 [`../system.md`](../system.md)를 확인한 뒤 실제 브랜치 상태를 점검한다.

## Current state

- AWS development 첫 배포가 완료됐다. PR #12 병합 커밋 `2a8e0f1`의 ECR digest `sha256:b3af0a3…9042daf5`로 EC2 healthy·digest 일치를 검증했다. API HTTPS와 Vercel 프록시의 allauth config가 200을 반환한다. 이후 `development` 배포의 현재 digest는 해당 CI run을 기준으로 확인한다. Production EC2는 아직 없다.
- [학습 목차](https://orange-taco.github.io/traceback-artifacts/)와 작성 스킬은 별도 `orange-taco/traceback-artifacts` 저장소에서 관리한다. iPad는 게시된 사이트에서 읽는다. Codex Cloud의 비공개 `TRACEBACK Study (3 repos)` 환경에 문서·백엔드·프런트 저장소를 연결해 게시했다. 사이트 내 수정 요청 기능은 아직 없다. 백엔드 저장소의 HTML 복사본과 Pages 워크플로는 제거한다.
- [인증 결정 가이드](https://orange-taco.github.io/traceback-artifacts/auth-session-allauth-guide.html#external-unlink)는 Kakao unlink의 부분 실패와 작업 복구 설계를 설명한다. 상태·작업 행과 재시도는 개선 설계로 아직 구현되지 않았다.
- SES 서울 리전에 `dev-traceback.com` 발신 도메인을 등록하고 Easy DKIM 검증을 완료했다. 개발 발신 주소는 `no-reply@dev-traceback.com`이며 전용 SMTP 계정 인증에 성공했다. RDS `traceback_app` 계정으로 실제 마이그레이션과 앱 DB health가 통과했다. 런타임 자격 증명은 EC2 root 전용 `.env`에 있다.
- 로컬 `.env`·`.env.dev`의 카카오 키 3개는 `traceback_dev-TEST` 앱과 일치한다. AWS 개발 EC2의 root 전용 `.env`에는 `traceback` 앱 키 3개와 RDS·SES 값이 설치됐다. 배포 callback URI도 카카오 콘솔에 등록했다.

## Validation / Next action

- 백엔드 CI run `39211302295`에서 Quality, Test, ECR publish, development EC2 deploy가 모두 성공했다. 실행 digest와 ECR digest 일치, 컨테이너 health, Django check, migration drift, 외부 TLS를 확인했다. 프런트 PR #10은 로그아웃 `/account` 오류를 수정했고 Vercel 운영 배포에서 `/auth/login` 이동을 재검증했다.
- 다음 작업은 SES 샌드박스 수신자 인증 또는 발송 권한 확대 후 이메일 가입·확인·로그인·탈퇴를 검증하고, 카카오 동의 화면 이후 로그인·연결 해제·탈퇴를 실제 계정으로 검증하는 것이다. 카카오 authorization 요청의 client ID·scope·API callback은 확인됐다. 순서는 [2번 배포 가이드](https://orange-taco.github.io/traceback-artifacts/2-dev-server-first-deployment.html)에 있다.

## Maintenance

- 이 문서에는 현재 상태, 검증 상태, 다음 작업만 짧게 유지한다.
- 선택적 미래 작업은 [`../todo.md`](../todo.md)에 둔다.
