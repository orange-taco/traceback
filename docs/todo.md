# TRACEBACK TODO

배포 전 사람이 AWS·GitHub에서 준비할 항목과 선택적 backlog를 기록한다. 상세 IAM
정책과 배포 검증 명령은 [`deployment.md`](deployment.md)를 따른다. 다음 세션의
필수 작업 목록은 아니며, 완료한 항목과 오래된 작업 이력은 남기지 않는다.
설계 결정은 이 문서가 아니라 [`system.md`](system.md) 또는
[`build-plan.md`](build-plan.md)에 기록한다.

## Phase 0: AWS·GitHub 배포 준비

아래 리소스는 아직 이 저장소의 workflow가 만들지 않는다. 실제 계정·리전·비용·네트워크
구성을 확인한 뒤 개발 환경부터 준비한다. 운영 환경은 개발 배포 검증 후 준비·승인한다.

- [ ] AWS 계정 ID, 리전, 예상 비용과 dev/prod VPC·서브넷·DNS 구성을 확정한다.
  EC2와 RDS는 환경별로 분리하고 RDS의 인터넷 공개 여부와 백업·복구 정책을 정한다.
- [ ] dev/prod용 RDS PostgreSQL과 DB 사용자·백업을 준비한다. RDS 보안 그룹의
  PostgreSQL 인바운드(5432)는 해당 환경 EC2 보안 그룹에서만 허용하고 연결을 확인한다.
- [ ] dev EC2를 생성하고 Docker Engine, Compose v2, AWS CLI v2, SSM Agent를 설치한다.
  dev RDS 연결, ECR 이미지 pull, SSM 명령 수신, 디스크 용량을 확인한다. 검증 후
  prod EC2를 별도 생성해 같은 항목을 확인한다.
- [ ] EC2 보안 그룹의 인바운드는 승인된 reverse proxy/TLS 경로에 필요한 포트만
  열고 SSH 공개 여부를 결정한다. 아웃바운드는 DB, SSM, ECR 및 이미지 저장소,
  SES 등에 필요한 경로를 확인한다. NAT와 VPC endpoint 중 사용할 방식을 정한다.
  운영 Compose의 app 포트는 호스트에 공개되지 않으므로 reverse proxy가 app에
  연결되는 방식을 먼저 확정한다.
- [ ] 환경별 EC2 instance profile에 SSM 관리 및 해당 ECR 저장소 pull 권한을
  부여한다. GitHub OIDC provider와 dev/prod 배포 IAM role을 만들고, role trust를
  해당 저장소·GitHub Environment로 제한한다. dev role에만 ECR push 권한을 준다.
- [ ] 같은 계정·리전에 ECR 저장소를 만들고 immutable tag 및 이미지 보존 정책을
  설정한다. dev/prod에서 같은 digest를 pull할 수 있는지 확인한다.
- [ ] GitHub `development`/`production` Environments를 만들고 브랜치 제한,
  `main` 보호 규칙 및 production 승인자를 설정한다. PR 필수 check는 현재
  `Quality`·`Test`·`Release branch gate` 기준으로 확인하고, 삭제된 별도
  `Production smoke` check 요구가 남지 않게 정리한다. 실제 계정·리전 확인 후
  `.env.dev.git`/`.env.prod.git`의 **비밀이 아닌 예시 값**을 갱신하고, 같은 값의
  `AWS_DEPLOY_ROLE_ARN`, `AWS_REGION`, `ECR_REPOSITORY`, 환경별 `*_INSTANCE_ID`를
  GitHub Environment variables에 등록한다. 예: dev EC2 생성 뒤 받은 instance ID를
  `DEVELOPMENT_INSTANCE_ID`에 입력한다. 템플릿 파일은 workflow가 읽지 않는다.
- [ ] 각 EC2의 추적되지 않는 `/opt/traceback/.env`에 `config/server.env.example`을
  참고해 서로 다른 DB URL·Django secret·도메인·SES·Kakao 값을 넣고 권한을 제한한다.
  DB 비밀번호나 API key를 `.env.dev.git`/`.env.prod.git` 또는 GitHub variables에
  커밋하지 않는다.
- [ ] reverse proxy·TLS·DNS·SES SMTP·Kakao callback을 연결하고 dev HTTP/DB
  smoke를 확인한다. 운영에서는 migration 영향과 DB 백업을 검토한 뒤 동일 ECR
  digest 승격 및 HTTP/DB smoke를 확인한다.

## Later: S3 storage

- [ ] 상품 이미지 등 파일 저장이 필요한 Phase에서 S3 사용 범위와 업로드 방식을
  결정한다. dev/prod 버킷 분리, 공개 접근 차단, 암호화, 최소 IAM 권한, CORS,
  수명주기·백업, CDN 연결 여부를 검토한다. 현재 로컬 파일 저장 경로에 S3를
  선제적으로 연결하지 않는다.

## Optional backlog

- [ ] abandoned account cleanup 정책 결정
  - 대상: 가입 미완료, 인증 정보 없음, SocialAccount 없음, 보존 기간 경과 계정
  - 결정 필요: 보존 기간, 삭제/익명화 범위, Celery 도입 시점
- [ ] Celery/background job과 queue 도입 여부 결정
- [ ] 활성 세션 목록과 전체 기기 로그아웃 UI 검토
- [ ] Phase 9+ coupon, notification, CS, address, preorder 상세 설계

## Maintenance

- backlog 항목은 새 세션마다 처리하지 않는다.
- 해당 영역의 task를 시작할 때만 관련 항목을 읽고, 필요하면 설계 결정으로 승격한다.
- 구현이 확정되면 항목을 삭제하고 `system.md` 또는 `build-plan.md`에 기록한다.
- Phase에 들어간 작업은 `build-plan.md`에서 관리한다.
