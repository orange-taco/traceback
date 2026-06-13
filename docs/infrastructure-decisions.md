# Infrastructure Decisions

이 문서는 애플리케이션 구현 전에 필요한 인프라 선택과 현재 결정을 기록한다.
구현 순서와 범위는 [`build-plan.md`](./build-plan.md)를 따른다.

## 확정

| 영역 | 결정 | 이유 |
| --- | --- | --- |
| Python 환경/의존성 | `uv`, `pyproject.toml`, `uv.lock` | 빠른 설치, 재현 가능한 lock, 로컬/CI/Docker 명령 통일 |
| 데이터베이스 | PostgreSQL | 운영 DB와 개발/CI 계약 통일 |
| 애플리케이션 서버 | Gunicorn + Uvicorn worker + Django ASGI | 프로세스 관리와 ASGI 실행 분리 |
| 이미지 배포 | 버전 tag에서 GitHub Actions가 GHCR production image 발행 | 배포 가능한 immutable artifact 확보 |
| 개발 데이터베이스 | Compose PostgreSQL | 운영과 SQL 동작 차이 최소화 |
| 개발 파일 저장소 | 로컬 파일 저장소 | 빠른 피드백, 오프라인 개발, 클라우드 비용/권한 불필요 |
| 운영 파일 저장소 | S3 호환 object storage | 다중 인스턴스와 영속 파일 지원 |
| 환경 구분 | local, staging, production | 개인 개발, 공유 검증, 실제 운영의 책임 분리 |
| AWS 사용 범위 | staging/production만 AWS 사용 | 상시 dev 서버와 staging의 역할 중복 방지 |
| AWS 애플리케이션 실행 | ECS Fargate + ALB | 서버 직접 관리 없이 container 배포, TLS/health/라우팅 제공 |
| AWS 데이터베이스 | 환경별 managed PostgreSQL | 백업, 장애 대응, 운영 DB 격리 |
| Reverse proxy | 별도 Nginx 서버 없이 ALB 사용 | 불필요한 서버 운영과 단일 장애 지점 제거 |

## 환경별 원칙

- 로컬 개발은 PostgreSQL과 로컬 파일 저장소를 기본값으로 사용한다.
- 로컬 PostgreSQL은 직접 설치본이 아니라 Compose service를 사용한다.
- 로컬에서는 development 실행과 production overlay smoke test를 모두 수행한다.
- 팀 공유 테스트, 외부 연동, S3 계약 검증은 AWS staging에서 수행한다.
- staging과 production은 DB, S3 bucket, secret, 배포 권한을 분리한다.
- CI 단위/통합 테스트는 PostgreSQL을 사용하고 외부 S3 호출은 하지 않는다.
- S3 연동 자체는 별도의 staging 통합 테스트에서 검증한다.
- 운영 비밀값은 저장소나 Compose 파일에 넣지 않고 배포 플랫폼 secret store에서 주입한다.
- `.env`는 로컬 개발 전용이며 Git에 포함하지 않는다.
- `.env.example`은 공개 가능한 변수 계약과 비밀이 아닌 placeholder만 포함한다.

## 미결정

| 영역 | 선택 시점 | 검토 기준 |
| --- | --- | --- |
| ECS 서비스/네트워크 상세 | 첫 staging 배포 전 | private subnet, NAT 비용, autoscaling, migration task |
| GHCR 또는 ECR 최종 선택 | 첫 staging 배포 전 | ECS pull 권한, 비용, image scanning |
| S3/CDN 상세 | 이미지 업로드 구현 전 | signed URL, CloudFront, 이미지 변환, 비용 |
| 비밀 관리 | 첫 staging 배포 전 | 배포 플랫폼 연동, 회전, 감사 로그 |
| 로그/오류 추적/APM | 첫 staging 배포 전 | 구조화 로그, trace ID, 알림, 보존 비용 |
| background job/queue | 비동기 작업 도입 전 | 재시도, 예약 실행, 운영 복잡도 |
