# TRACEBACK TODO

지금 해야 할 일과 이후에 할 일을 함께 모은 순서 목록이다. Phase 범위·완료 기준은
[`build-plan.md`](build-plan.md), 실제 AWS/Vercel 설정값과 현재 확인 상태는
[`deployment.md`](deployment.md), 처음 배포하는 사람을 위한 그림·설명은
[2번 첫 배포 가이드](https://orange-taco.github.io/traceback-artifacts/2-dev-server-first-deployment.html#launch-order)에 둔다.
완료한 설정을 이 목록에 길게 복사하지 않고, 남은 작업만 체크한다.

## 1. 개발 환경 첫 실사용까지

1. [ ] **비용과 네트워크 최종 점검** — AWS Budget 알림과 실제 사용액을 확인한다.
   EC2·RDS·EIP·Route 53·ECR 예상 비용을 계산하고, EC2 아웃바운드·NACL·
   RDS 5432·라우팅 테이블을 현재 구성에 맞게 다시 확인한다. 개발 테스트가 끝나면
   RDS/EC2를 중지하는 운영 습관을 정한다.
2. [ ] **EC2 배포 기반 준비** — 개발 EC2 역할에 해당 ECR 저장소의 pull 권한을
   추가한다. SSM으로 접속해 Docker Engine, Compose v2, AWS CLI v2와
   `/opt/traceback` 배포 디렉터리를 준비한다.
3. [ ] **RDS·서버 환경변수 연결** — 앱 전용 PostgreSQL 사용자·DB를 만들고,
   RDS 백업/복구 지점을 확인한다. 개발 EC2의 미추적 `/opt/traceback/.env`에
   `config/server.development.env.example`을 기준으로 DB URL, Django secret,
   API/Vercel 주소, SES·Kakao 값을 채운 뒤 EC2→RDS 연결을 검증한다.
4. [ ] **API HTTPS와 역방향 프록시** — `api.dev-traceback.com`의 HTTP 검증 경로를
   제공하고 TLS 인증서를 발급한다. 갱신을 시험한 뒤 호스트 Nginx 설정을
   활성화해 `127.0.0.1:8000` Django로 전달하도록 준비한다. 인증서와 외부
   443 연결을 확인한다. 앱 배포 전의 502 응답은 다음 단계에서 해결한다. 자세한 순서는
   [인증서·Nginx 절](https://orange-taco.github.io/traceback-artifacts/2-dev-server-first-deployment.html#https-sequence)을 따른다.
5. [ ] **개발 자동 배포 검증** — PR을 `development`에 병합한 뒤 CI의
   Quality/Test → GitHub OIDC → ECR image push → SSM → EC2 Compose·migration
   흐름을 확인한다. image digest, 앱 health check와 외부 HTTPS
   `/_allauth/browser/v1/config`의 200 응답을 각각 검사한다.
   ECR 보존 정책은 운영 승격·rollback에 필요한 digest를 지우지 않게 정한다.
6. [ ] **Vercel 경유 브라우저 인증 검증** — 개발 Vercel 프로젝트의 Production
   범위 `DJANGO_ORIGIN`은 재배포로 적용됐다. 현재 API HTTPS 연결이 안 되어
   인증 경로가 502를 반환한다. 서버 연결 후 `/_allauth`, `/accounts`, `/api`,
   쿠키·CSRF, 이메일 가입/로그인/탈퇴와 Kakao
   callback·연결 해제를 브라우저에서 검사한다. Preview URL은 별도 CSRF·OAuth
   정책을 정할 때 연결한다.

## 2. 운영 환경을 준비할 때

7. [ ] **독립된 운영 인프라** — 별도 production EC2·RDS·보안 그룹·도메인/TLS,
   서버 `.env`, GitHub `production` Environment와 제한된 OIDC 역할을 만든다.
   별도 Vercel production 프로젝트·API origin을 연결한다. production S3 버킷도
   private·암호화·public access 차단으로 준비한다.
8. [ ] **동일 이미지 승격·운영 검증** — `development`에서 성공한 ECR digest를
   `main` 배포에 그대로 사용한다. 운영 DB 백업·migration, Nginx/HTTPS,
   SES·Kakao·브라우저 인증과 외부 API를 확인한다.

## 3. 기능이 필요해질 때

9. [ ] 상품 이미지 업로드 기능을 구현할 때 S3 저장 방식, 필요한 bucket/prefix의
   최소 IAM 권한, CORS와 이미지 제공 방식(CDN 포함)을 정하고 연동한다.
10. [ ] 가입 미완료 계정 정리 정책과 필요 시 Celery 도입을 결정한다.
11. [ ] 활성 세션 목록·전체 기기 로그아웃 UI를 검토한다.
12. [ ] 이후 Phase에서 coupon·notification·CS·address·preorder를 설계한다.

`.env.dev.git`·`.env.prod.git`은 GitHub Environment 변수의 예시 목록이며 workflow가
직접 읽지 않는다. DB 비밀번호·API key는 커밋하지 않고 각 EC2의
`/opt/traceback/.env`에 보관한다.
