# TRACEBACK TODO

배포 준비는 아래 순서로 진행한다. AWS/GitHub의 구체적인 설정값과 검증 명령은
[`deployment.md`](deployment.md)를 따른다. 실제 리소스 생성과 비용 발생 전에는
계정·리전·비용을 확인한다.

## Phase 0 배포 준비

1. [ ] **공통 설계 확인** — AWS 계정·리전·예상 비용, dev/prod 네트워크와 DNS,
   EC2↔RDS 및 reverse proxy 연결 방식, RDS 공개 여부·SSH 접근·NAT/VPC endpoint,
   DB 백업·복구와 ECR 이미지 보존 기간을 정한다.
2. [ ] **개발 AWS 구축** — dev RDS PostgreSQL·EC2와 공용 ECR(immutable tag)을
   준비한다. 보안 그룹은 RDS 5432를 dev EC2에서만 허용하고, EC2 인바운드는
   승인된 웹 경로로 제한한다. 아웃바운드 DB·SSM·ECR·SES 경로를 확인한다.
   EC2에 Docker·Compose·AWS CLI·SSM Agent를 설치하고, instance role(SSM·ECR pull),
   GitHub OIDC provider와 dev 배포 role(ECR push·SSM)을 연결한다.
3. [ ] **개발 설정·배포 검증** — GitHub `development` Environment를 만들고 브랜치를
   제한한다. 확인된 `AWS_REGION`, `ECR_REPOSITORY`, `AWS_DEPLOY_ROLE_ARN`,
   `DEVELOPMENT_INSTANCE_ID`를 GitHub Environment variables에 등록한다.
   예: EC2 생성 후 받은 ID를 `DEVELOPMENT_INSTANCE_ID`에 넣고 `.env.dev.git`의
   비밀이 아닌 예시 값도 맞춘다. EC2의 `/opt/traceback/.env`에는 별도로 dev DB URL,
   Django secret·도메인·SES·Kakao 값을 넣는다. dev CI/SSM 배포, migration,
   reverse proxy·TLS 및 외부 HTTP/DB·메일·Kakao 동작을 확인한다.
4. [ ] **운영 AWS·GitHub 구축** — dev와 분리된 prod RDS·EC2·보안 그룹 및
   `/opt/traceback/.env`를 2~3번과 같은 기준으로 준비하고 연결·백업을 확인한다.
   prod EC2 role에는 SSM·ECR pull, prod GitHub OIDC role에는 SSM·ECR 조회
   권한만 준다. GitHub `production` Environment의 `AWS_REGION`, `ECR_REPOSITORY`,
   `AWS_DEPLOY_ROLE_ARN`, `PRODUCTION_INSTANCE_ID`를 등록하고 `.env.prod.git`의
   비밀이 아닌 예시 값도 맞춘다. `main` 브랜치 보호, 현재 필수 CI check 및 운영
   배포 승인자를 설정하고 예전 `Production smoke` check 요구는 제거한다.
5. [ ] **운영 승격 검증** — migration 영향과 DB 백업을 검토한 뒤 개발에서 성공한
   ECR digest를 그대로 운영에 배포한다. 운영 reverse proxy·TLS와 외부 HTTP/DB,
   SES·Kakao를 확인한다.

`.env.dev.git`·`.env.prod.git`은 GitHub 변수의 추적 가능한 예시 목록이며 workflow가
직접 읽지 않는다. DB 비밀번호·API key 등은 커밋하지 않고 각 EC2의 추적되지 않는
`/opt/traceback/.env`에 보관한다.

## 이후 필요할 때

- [ ] 상품 이미지 저장을 구현할 때 S3 범위와 업로드 방식을 결정하고, 환경별 버킷·
  공개 접근 차단·암호화·IAM 권한·CORS·수명주기·CDN을 검토한다.
- [ ] 가입 미완료 계정 정리 정책(대상·보존 기간·삭제 범위)과 필요 시 Celery 도입을
  결정한다.
- [ ] 활성 세션 목록과 전체 기기 로그아웃 UI를 검토한다.
- [ ] 추후 Phase에서 coupon·notification·CS·address·preorder를 설계한다.
