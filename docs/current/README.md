# Current Work

새 AI 세션은 이 문서와 [`../system.md`](../system.md)를 먼저 읽는다.

## Current state

- Phase 0 Foundation의 account/auth 서버 slice가 구현되어 있다.
- development 배포 설정은 PR [#12](https://github.com/orange-taco/traceback/pull/12), AWS 학습 아티팩트는 PR [#13](https://github.com/orange-taco/traceback/pull/13)에 있다. 둘 다 `development`에서 분기했고 아직 merge하지 않았다. 두 PR의 `Quality`와 `Test`는 통과했으며 배포 job은 PR에서 실행되지 않았다.
- Kakao provider unlink, account deletion, 사용자별 세션 추적이 구현되어 있다.
- 로컬 메일은 console, AWS development/production 메일은 SES SMTP를 사용한다. `.env.example`과 `config/server.env.example`에 SES 인증 변수 이름을 명시했다.
- `development`/`main` push의 quality·test 성공 뒤에만 배포 job이 호출된다. Development는 SHA 이미지가 이미 있으면 재사용하고, production은 성공한 development CI의 SHA로 조회한 동일 digest를 승격한다. EC2는 이미지 속 Compose 파일을 반영하고 migration 후 HTTP/DB healthcheck가 통과한 앱을 실행한다.
- `.env.dev.git`/`.env.prod.git`는 GitHub Environment 변수 목록이고,
  EC2 `/opt/traceback/.env` 예시는 development/production별로 분리했다. AWS/GitHub 수동 설정은 `docs/deployment.md`에 정리했다.
- AWS development는 서울 리전에 dev EC2와 private S3를 생성했다. EC2는 `t3.micro`, SSH 미개방, SSM 역할이며 Docker/app 배포 전이다. 기본 Session Manager 접속과 SSM Run Command는 EC2 사용 추가 요금이 없다. 선택형 세션 로그 저장이나 유료 SSM 기능은 별도 과금될 수 있다. RDS PostgreSQL 17.11 `db.t4g.micro` Single-AZ가 사용 가능하며 인터넷 액세스가 비활성화됐다. EC2 전용 security group에서만 RDS TCP 5432를 허용한다. 개발·AWS 테스트 중에만 RDS를 켜고 작업 후 중지한다. 생성 화면 추정은 실행 시간·20 GiB storage 기준 USD 20.87/월이다. AWS 계정은 PAID plan에 USD 100 credit이 남아 있으나 지출 한도는 아니다. S3 업로드 코드와 앱 권한은 아직 없다.
- GitHub development 배포 준비: `development` Environment에 브랜치 제한을 걸고 네 변수를 등록했다. AWS 계정에 GitHub OIDC provider, 개발 전용 `traceback-development-deploy` 최소 권한 역할, private ECR `traceback`(불변 태그/AES-256)을 만들었다. ECR은 아직 비어 있고, EC2 instance role의 ECR pull 권한과 Docker bootstrap은 남아 있다. GitHub development branch protection에서 PR과 `Quality`/`Test` 통과를 요구한다. 이 설정은 development push로 아직 검증하지 않았다.
- Route 53 `dev-traceback.com`은 ACTIVE 등록 상태이고 hosted zone 네임서버와 등록 네임서버가 일치한다. EIP `3.34.78.140`을 Development EC2에 연결했고 `api.dev-traceback.com` A 레코드(TTL 300초)를 생성했다. EIP는 EC2 중지 중에도 시간당 요금이 발생한다. Nginx·TLS와 백엔드 앱은 아직 배포되지 않았다.
- 프런트엔드 호스팅은 Vercel이다. `traceback-client` Vercel project가 client 저장소에 연결됐고 Production branch는 development로 설정했다(현재 개발 환경 전용). `https://traceback-client-nine.vercel.app`에서 commit `850b255`의 SSR이 HTTP 200으로 동작한다. Vercel project Environment Variables는 현재 0개이며, `DJANGO_ORIGIN`은 API HTTPS가 준비된 뒤 Production Environment에 등록한다. allauth 설정 요청은 Django origin 미연결 상태라 404이며, AWS development 서버 배포 후 same-origin 인증 경로·CSRF·Kakao callback 검증이 남아 있다. client의 `.env.dev`에는 frontend origin을 기록했고 Django origin은 비어 있다. Production용 별도 Vercel project는 나중에 만든다.
- `visualizations/index.html`은 전체 구조·인증·CI/CD·워크플로 전체 코드의 진입점이다. System Guide는 세 워크플로 YAML의 모든 줄(127+87+79줄)을 구간별 원문과 해설로 보여준다.
- EC2 접속 학습 자료는 [aws-ssm-ssh-learning-guide.html](../artifact/aws-ssm-ssh-learning-guide.html)이다. 일반 네트워크의 SSH/포트/방화벽 개념과 AWS의 SSM/IAM/보안 그룹을 나눠 설명하고, 현재 dev EC2용 AWS CLI SSO 설정 절차를 담았다.
- 첫 개발 서버 구축, GitHub Actions OIDC·IAM·ECR, `deploy-ec2.sh` 전체 코드 해설, 로컬 수동 ECR push→SSM 배포, Docker volume 차이, 파일별 CI/CD 읽기 순서는 [dev-server-first-deployment.html](../artifact/dev-server-first-deployment.html)에 시각화했다.
- DNS 기초와 패킷 왕복, Root/Anycast, 캐시, Route 53·Cloudflare·가비아 비교, 고정/유동 IP 선택과 유동 IP용 DNS 자동화 대안은 [dns-resolution-map.html](../artifact/dns-resolution-map.html)에 정리했다.
- 현재 AWS EIP·Route 53 설정과 IP/도메인/DNS 개념은 [development-ip-domain-guide.html](../artifact/development-ip-domain-guide.html)에 시각화했다. 환경변수 저장 위치와 비밀값 분리는 첫 배포 가이드의 전용 절에서 다룬다.
- 네 AWS 학습 HTML은 운영체제의 다크 모드 설정과 관계없이 항상 밝은 테마를 사용한다.

## Validation

- Backend PostgreSQL 17 Docker suite 40 passed, 96.23% coverage. Ruff, format, mypy, YAML lint, Django development settings check, local/production Compose config 통과. EC2용 Compose 앱 포트가 `127.0.0.1:8000`으로만 노출됨을 확인했다. Client typecheck와 SSR build 통과.
- Vercel development deployment에서 home과 login SSR 페이지 HTTP 200, 브라우저 렌더링을 확인했다. `/_allauth/browser/v1/config`는 backend 미배포로 HTTP 404다.
- HTML의 링크와 스크립트 문법, 브라우저의 탭·상세 설명 동작을 확인했다. 세 YAML 원문의 줄 번호와 전체 범위를 대조했다.
- DNS 아티팩트는 HTML 구조와 고유 ID 20개, 3개 탭/패널 연결, JavaScript 문법, `git diff --check`를 통과했다. 데스크톱·390px 모바일 화면에서 탭 전환, 선택 탭 자동 표시, 페이지 가로 넘침 없음, 브라우저 콘솔 오류 없음을 확인했다. 한국어 제목 줄바꿈과 참고 링크 목록을 정리했고, 선택한 EIP 운영 상태를 반영했다.
- 개발 주소 아티팩트는 실제 AWS 설정, 환경변수 저장 위치와 비밀값 분리, GitHub OIDC 배포 흐름을 설명한다. HTML 구조·내부 링크와 JavaScript 문법을 확인했고 Playwright에서 4개 환경 설명, 설정 흐름, 모바일 가로 넘침 없음, 콘솔 오류 없음을 확인했다.
- 네 AWS 학습 HTML의 로컬 링크·fragment·JavaScript 구문과 `git diff --check`를 확인했다. Playwright에서 네 문서를 390px/1440px로 열어 가로 넘침이 없고 브라우저 오류가 없는 것을 확인했다. 첫 배포 문서에는 호스트 Nginx, Nginx 컨테이너, ALB, 전용 Nginx EC2의 요청 흐름 그림과 네트워크 용어 설명을 추가했다.
- 첫 배포 안내에 GitHub/AWS 실제 설정 화면 10개를 캡처했다. Environment 변수·OIDC provider·두 IAM 역할·ECR·branch protection 화면과 안내 글의 이미지/내부 링크를 확인했다. Playwright에서 390px/1440px 레이아웃, 화면 넘침, 이미지 로드와 브라우저 오류를 점검했다.
- `deploy-ec2.sh`는 입력값 검증 후 Bash 명령 배열을 SSM JSON으로 직렬화한다. `bash -n`과 jq 명령 배열 직렬화를 확인했다. 실제 SSM/ECR/EC2 배포는 서버 ECR pull 권한·Docker·`.env`가 준비되지 않아 아직 실행하지 않았다.
- EC2의 SSM Agent Online, 인스턴스 프로파일, SSH 미개방 보안 그룹을 확인했다. 로컬 AWS CLI에서 Identity Center `traceback-dev` 프로필로 계정 968579693658의 SSM 세션을 열었고, `aws ssm traceback-dev` zsh 단축 명령을 추가했다. GitHub OIDC/ECR 준비는 완료했다. EC2 ECR pull 권한, Docker bootstrap, 앱 배포는 남아 있다. RDS와 private S3는 생성됐으며 RDS는 개발·AWS 테스트 중에만 실행한다.

## Next action

- Development 설정에서 `DEBUG=False`, 명시적 allowed hosts, CSRF trusted origins, secure cookies를 적용했다. 배포 스크립트는 Compose 기본 파일과 prod overlay를 병합하며 앱은 EC2 localhost에만 publish한다. 첫 배포 가이드에 GitHub Actions OIDC, IAM 역할 생성·신뢰/권한 정책, ECR 요금, GitHub Environment 변수와 설정 화면 캡처를 추가했다. DNS/EIP, GitHub development 환경, AWS OIDC/ECR, development branch protection(PR 및 `Quality`/`Test` 통과 요구)은 설정했다. 다음은 EC2 instance role의 ECR pull 권한과 Docker/Compose/AWS CLI bootstrap이다. 이후 RDS 앱 DB 계정, 런타임 `.env`, Nginx 설치·TLS, Vercel 변수, 브라우저 auth 검증이 남아 있다. 전체 순서는 위 아티팩트를 참고한다. RDS는 개발·AWS 테스트 중에만 켜고 작업 후 중지한다.
- Production은 개발에서 성공한 source SHA·image digest·migration 영향을 확인하고, 별도 Vercel/AWS 환경을 만든 뒤 명시적 승인 후 배포한다.

## Maintenance

- 이 문서는 현재 상태·검증·다음 세션 진입점만 유지한다.
- 선택적 미래 backlog는 [`../todo.md`](../todo.md)에서 관리한다.
