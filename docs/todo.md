# TRACEBACK TODO

배포 준비는 아래 순서로 진행한다. AWS/GitHub의 구체적인 설정값과 검증 명령은
[`deployment.md`](deployment.md)를 따른다. 실제 리소스 생성과 비용 발생 전에는
계정·리전·비용을 확인한다.

## Phase 0 배포 준비

1. [ ] **Vercel 환경별 backend 연결** — development 프로젝트 `traceback-client`의
   SSR 배포와 기본 URL은 확인했다. 현재 이 프로젝트의 Production Branch는
   `development`이며 Vercel 환경변수는 아직 0개다. HTTPS API가 준비되면
   `DJANGO_ORIGIN=https://api.dev-traceback.com`을 이 프로젝트의 Production scope에
   등록하고 재배포한다. Preview scope는 PR 미리보기에서 dev API를 쓸지 정한 뒤 설정한다.
   Development scope는 `vercel dev`를 사용할 때만 등록하고, 일반 로컬 Vite 실행은
   client의 로컬 proxy 설정을 사용한다. `.env.dev` 파일은 Vercel에 자동 업로드되지 않는다.
   배포 후 `/_allauth`·`/accounts`·API, same-origin session/CSRF, email, Kakao callback을
   검증한다. Production은 별도 Vercel project와 production API origin으로 나중에 구성한다.
2. [ ] **공통 AWS 설계·요금 확인** — 계정의 PAID plan과 남은 USD 100 credit을
   확인했다. credit은 지출 한도가 아니다. RDS를 켜 두면 트래픽이 없어도 현재
   콘솔 추정 USD 20.87/월(instance + 20 GiB storage)이 발생한다. EC2와 합산한
   전체 예상액 및 AWS Budget 알림을 정리하고 실제 사용량을 확인한다. 개발·AWS
   테스트 중에만 RDS를 켜고 작업 종료 후 중지한다. dev/prod
   네트워크·DNS, Vercel↔EC2 TLS 경로, EC2↔RDS 연결, DB 복구와 ECR 보존 기간을
   정한다. 개발 초기에는 NAT Gateway와 Load Balancer를 피하고, 계정에 적용되는
   무료 한도를 넘는 비용이 생기는지 생성 전 AWS Pricing Calculator로 확인한다.
3. [ ] **개발 AWS 구축** — 서울 리전에 EC2 `t3.micro`와 private S3 버킷을 생성했다.
   EC2는 SSH 없이 SSM 접속하도록 했고, 인바운드는 HTTP/HTTPS만 허용한다. S3는
   public access 차단·ACL 비활성화·SSE-S3 상태다. RDS는 PostgreSQL 17.11,
   `db.t4g.micro`, Single-AZ, private, 20 GiB, 자동 확장 꺼짐으로 생성했다. RDS는
   사용 가능 상태이며 `rds-ec2-1`이 `ec2-rds-1` source에서만 TCP 5432를 허용하고,
   연결된 EC2는 `i-051f85a1ac4e64a2c`다. 개발·AWS 테스트 중에만 RDS를 켜고 작업 후
   중지한다. EIP `3.34.78.140`을 dev EC2에 연결했고 Route 53에
   `api.dev-traceback.com` A 레코드(TTL 300초)를 만들었다. 도메인은 ACTIVE이고 등록
   네임서버가 hosted zone과 일치한다. EIP는 EC2 중지 중에도 공인 IPv4 요금이 발생한다.
   Seoul private ECR `traceback` 저장소를 생성했고 태그 불변/AES-256을 확인했다. 아직 이미지가 없다.
   업로드 기능 구현 전에는 버킷만 만들고, 앱의 S3 접근 IAM 권한은 필요한 prefix와
   동작이 확정될 때 EC2 instance role에 최소 권한으로 추가한다. 보안 그룹은 RDS
   5432를 dev EC2에서만 허용하고, EC2 인바운드는 승인된 웹 경로로 제한한다.
   아웃바운드 DB·SSM·ECR·SES 경로를 확인한다. EC2 instance role에는 현재 SSM 권한만
   있다. 이 role에 ECR pull 권한을 추가한 다음 EC2에 Docker·Compose·AWS CLI를
   설치하고 `/opt/traceback`을 준비한다. GitHub OIDC provider와 개발 배포 role
   (ECR push·SSM)은 생성했다. 개발 역할의 신뢰 조건은 TRACEBACK 저장소의
   `development` Environment로 제한했다.
4. [ ] **개발 설정·배포 검증** — GitHub `development` Environment를 만들고
   `development` 브랜치만 허용하도록 제한했다. `AWS_REGION`, `ECR_REPOSITORY`,
   `AWS_DEPLOY_ROLE_ARN`, `DEVELOPMENT_INSTANCE_ID` 네 Environment variables를
   등록했고 `.env.dev.git`과 맞췄다. ECR/OIDC/환경변수는 준비됐지만 개발 브랜치 push로
   배포를 검증하지 않았다. `development` branch protection은 PR과 `Quality`/`Test`
   통과를 요구하고 force push·브랜치 삭제를 막도록 설정했다(승인 리뷰는 1인 유지보수 흐름에
   맞춰 요구하지 않음). EC2의 `/opt/traceback/.env`에는 별도로 dev DB URL,
   Django secret·도메인·SES·Kakao 값을 넣는다. dev CI/SSM 배포, migration,
   reverse proxy·TLS 및 외부 HTTP/DB·메일·Kakao 동작을 확인한다.
5. [ ] **운영 AWS·GitHub 구축** — dev와 분리된 prod RDS·EC2·보안 그룹 및
   `/opt/traceback/.env`를 개발 구축 단계와 같은 기준으로 준비하고 연결·백업을 확인한다.
   prod EC2 role에는 SSM·ECR pull, prod GitHub OIDC role에는 SSM·ECR 조회
   권한만 준다. GitHub `production` Environment의 `AWS_REGION`, `ECR_REPOSITORY`,
   `AWS_DEPLOY_ROLE_ARN`, `PRODUCTION_INSTANCE_ID`를 등록하고 `.env.prod.git`의
   비밀이 아닌 예시 값도 맞춘다. `main` 브랜치 보호, 현재 필수 CI check 및 운영
   배포 승인자를 설정하고 예전 `Production smoke` check 요구는 제거한다.
6. [ ] **운영 승격 검증** — migration 영향과 DB 백업을 검토한 뒤 개발에서 성공한
   ECR digest를 그대로 운영에 배포한다. 운영 Vercel 도메인·백엔드 경로와 reverse
   proxy·TLS, 외부 HTTP/DB, SES·Kakao를 확인한다.

`.env.dev.git`·`.env.prod.git`은 GitHub 변수의 추적 가능한 예시 목록이며 workflow가
직접 읽지 않는다. DB 비밀번호·API key 등은 커밋하지 않고 각 EC2의 추적되지 않는
`/opt/traceback/.env`에 보관한다.

## 이후 필요할 때

- [ ] 상품 이미지 업로드를 구현할 때 development S3 버킷 연동을 추가한다. 업로드 방식,
  EC2 IAM 최소 권한, CORS 필요 여부, 이미지 전달 방식(CDN 포함)을 구현 요구에 맞게 정한다.
- [ ] Production AWS 구축 시 dev와 분리된 private S3 버킷을 만든다. public access 차단,
  기본 암호화, 업로드 기능에 필요한 최소 IAM 권한을 확인한다.
- [ ] 가입 미완료 계정 정리 정책(대상·보존 기간·삭제 범위)과 필요 시 Celery 도입을
  결정한다.
- [ ] 활성 세션 목록과 전체 기기 로그아웃 UI를 검토한다.
- [ ] 추후 Phase에서 coupon·notification·CS·address·preorder를 설계한다.
