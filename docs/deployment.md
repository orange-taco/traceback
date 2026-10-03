# AWS deployment setup (manual, before first deployment)

This runbook covers the confirmed GitHub-hosted runner → OIDC → ECR/SSM → separate EC2/DB path. No AWS resource is created by this repository. Infrastructure creation, production deployment, and any change with a cost require the owner's separate approval.

## Frontend hosting decision

The client is hosted on Vercel with React Router SSR. Django remains on the separate
development and production EC2 instances; do not create frontend EC2 instances. S3 is
for uploaded objects, not the SSR application. The intended browser contract remains
same-origin: `traceback-client/vercel.ts` forwards `/_allauth`, `/accounts`, and `/api`
to `DJANGO_ORIGIN` when that HTTPS origin is configured in the Vercel project. The
development project's `DJANGO_ORIGIN` is saved in its Production scope but needs a
fresh deployment after API HTTPS is ready. Confirm
cookie/CSRF forwarding and Kakao OAuth callback behavior in browser QA before treating
a Vercel deployment as ready. Vercel projects, domains, branch mappings, and any paid
plan are configured manually.

## Development database and object storage

Create a development RDS PostgreSQL instance and a private S3 bucket as part of
the first AWS development setup. Keep the RDS instance non-public; permit inbound
TCP 5432 only from the development EC2 security group. Enable RDS automated
backups with a retention period appropriate for development and confirm the
restore path before applying migrations.

Keep S3 Block Public Access enabled and default encryption enabled. The bucket
is groundwork for future product uploads; the current app has no S3 upload
integration. Do not grant the EC2 role S3 access until upload behavior is
implemented; then scope object permissions to the required bucket and prefix.
Create a separate private bucket for production when production infrastructure
is prepared. Do not use S3 to host the React Router SSR application.

The development bucket has been created in Seoul as
`traceback-development-assets-968579693658-ap-northeast-2`. It is empty, has
S3 Block Public Access enabled, ACLs disabled, and SSE-S3 default encryption.
No application IAM permission or upload integration is configured.

On 2026-09-27, the AWS console reported the account plan as `PAID` with an
active Free Tier credit balance. Credits reduce eligible bills but are not a
spending cap; EC2/RDS usage can be charged after credits are exhausted.

The development EC2 was created in Seoul on 2026-09-27 as
`traceback-development-app` (`i-051f85a1ac4e64a2c`): Amazon Linux 2023 x86,
`t3.micro`, 20 GiB gp3, public subnet/IP, and Standard CPU credits. Its
`traceback-development-app` security group allows TCP 80/443 from the internet,
has no SSH rule, and retains the default outbound allow rule. The
`traceback-development-ec2` instance profile has `AmazonSSMManagedInstanceCore`;
ECR pull access is still pending and belongs on this EC2 role, not the GitHub
deploy role described below. The instance is running and has not yet been
bootstrapped with Docker or the application.

On 2026-10-03, Elastic IP `3.34.78.140` (`eipalloc-07ecd0df0cc7e83bd`) was
allocated in `ap-northeast-2`, tagged `Name=traceback-development-eip`, and
associated with this EC2 instance's primary private address. Route 53 domain
`dev-traceback.com` is `ACTIVE`; its registered name servers match the public
hosted zone. The zone now has `api.dev-traceback.com A 3.34.78.140` with a
300-second TTL. The record resolves to the EC2 address, but Nginx, TLS, and the
application are not installed yet.

The RDS instance was created on 2026-09-27 and is `Available`. Its endpoint is
`traceback-development-db.cdgccc6q6aoe.ap-northeast-2.rds.amazonaws.com`. The
configuration is PostgreSQL 17.11,
`db.t4g.micro`, Single-AZ, 20 GiB gp3, encrypted, non-public, one-day automated
backup retention, and no storage autoscaling or paid enhanced monitoring. The
RDS security group `rds-ec2-1` has one inbound PostgreSQL/TCP 5432 rule whose
source is the EC2-only `ec2-rds-1` security group. RDS reports one connected
compute resource, `i-051f85a1ac4e64a2c`. The connection panel shows internet
access disabled. The creation estimate was USD 20.87/month for the RDS instance
and allocated storage alone, before excluded backup, I/O, or transfer costs.
This charge accrues while the instance is running even with no application
traffic. [AWS documents](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html)
that a stopped RDS instance avoids instance-hour charges but continues to bill
storage/backups and automatically starts after seven consecutive stopped days.

## Cost-conscious development defaults

First check the account's creation date, Free or Paid plan, remaining credits,
and service eligibility in Billing. AWS's current Free account plan is limited
to six months or until credits are exhausted; the account is then closed unless
upgraded. On a Paid plan, credits offset eligible charges but usage beyond
credits is billable. Older accounts may have different legacy Free Tier terms.
Do not assume that a resource is free from its instance type alone.

For a small development workload, use one x86 `t3.micro` EC2 to match
the current `linux/amd64` image, and one Single-AZ `db.t4g.micro` PostgreSQL
instance. Keep database storage at the minimum the selected RDS configuration
allows, skip Multi-AZ, and increase instance size only if observed memory or
database pressure requires it. A micro EC2 has limited memory; check container
health and memory after deployment.

Avoid a NAT Gateway and load balancer for this single development host. A NAT
Gateway has an hourly and data-processing charge; AWS currently lists public
IPv4 at USD 0.005 per hour (about USD 3.65 per month for one continuously used
address, before tax). Put the EC2 in a public subnet for required outbound
access and the Vercel HTTPS origin, restrict inbound rules to the required web
ports, administer it through SSM rather than opening SSH, and keep RDS private
with TCP 5432 allowed only from the EC2 security group. This saves fixed network
costs while keeping the database off the public internet.

Session Manager cost note: AWS does not add a per-session charge when Session
Manager is used with Amazon EC2, and Run Command has no additional charge on
EC2. This development host and the CI/CD SSM deployment target are native EC2
instances, so basic interactive SSM access and deployment commands do not add
an SSM session/invocation fee. Optional features and integrations can still
cost money, such as just-in-time node access or storing session logs in
CloudWatch Logs/S3; check their service pricing before enabling them. As of
2026-09-30, the listed USD 0.05 per Session Manager session and USD 0.002 per
Run Command invocation apply to hybrid/multicloud nodes, not this AWS EC2 host.
See the [AWS Systems Manager pricing page](https://aws.amazon.com/systems-manager/pricing/).

Create an AWS Budget/credit alert and review actual usage after deployment. For
development, keep RDS running only while actively developing or testing against
the AWS environment, and stop it when that work is finished. Do not leave the
development RDS running between work sessions. Stopping it saves instance-hour
charges but not storage or backup charges. Stop the EC2 as well when it is not
needed. Development uses an Elastic IP so its API DNS record stays valid after
restart; the EIP continues to incur the public IPv4 hourly charge while the EC2
is stopped. An automatically assigned public IPv4 is released at stop and avoids
that address charge until the instance starts again. RDS may automatically restart
after seven consecutive stopped days.
Remember that public IPv4, ECR image storage, data transfer, RDS storage/backups,
S3 requests/storage, DNS, and logs can still incur charges depending on account
eligibility and usage. Use the AWS Pricing Calculator with the target Region
before creating billable resources.

## Development frontend deployment status

The Vercel project `traceback-client` is connected to
`orange-taco/traceback-client` on the Hobby plan. Its Production branch is
currently set to `development` because this project is serving development
only; create a separate project for production later. The current Vercel URL is
`https://traceback-client-nine.vercel.app`. Production deployment `Da65k8bCs`
rebuilt development commit `afd7664` on 2026-10-04 with
`DJANGO_ORIGIN=https://api.dev-traceback.com` in its Production environment.
The deployment is Ready. The auth config request
`/_allauth/browser/v1/config` changed from a React Router 404 to a Vercel 502:
the rewrite is active, but `api.dev-traceback.com:443` still refuses connections.
Deploy Nginx/TLS and Django, then verify session, CSRF, email, and Kakao.
The `.env.dev` frontend origin is recorded locally in the client repository;
`.env.prod` remains unset.

Vercel has separate Development, Preview, and Production variable scopes. In
this development-only project, the Production scope applies to deployments from
the `development` production branch. The Production value is active in the new
deployment. The Preview scope is
for other branches and pull request previews; leave it unset until preview URLs
are included in Django's CSRF trusted-origin and OAuth redirect/callback policies.
`DJANGO_ALLOWED_HOSTS` controls Django request hostnames and is configured
separately; it is not the prerequisite for setting the frontend origin itself. The
Development scope is used with `vercel dev`/Vercel CLI environment pulling; the
ordinary local Vite proxy is configured separately. A local `.env.dev` file is
not uploaded to Vercel. The current frontend `vercel.ts` consumes only
`DJANGO_ORIGIN`; do not put Django, database, SES, or Kakao secrets in Vercel.

## Public learning guides

GitHub Pages is enabled for `https://orange-taco.github.io/traceback/` with a
GitHub Actions publishing source. The `github-pages` environment permits only
the `development` branch. `.github/workflows/artifact-pages.yml` publishes only
`docs/artifact/` after changes reach `development`; the site is not live until
that workflow runs successfully. `docs/artifact/index.html` is the single mobile
entry point. The packaging script converts links to source files outside the
artifact directory into revision-specific GitHub links. The screenshots were
reviewed before publication: they show AWS account/resource identifiers and
GitHub settings, but no password, token, or private contact detail.

## Current delivery contract

1. `development` push runs `quality` and `test` in `ci.yml`. Both must pass before the called development workflow builds a production-target image, tags it with the development commit SHA, pushes it to ECR, and deploys its **digest** through SSM.
2. A `development → main` PR runs the production-container smoke test within `quality`: it starts the built image, migrates a temporary SQLite database and waits for its HTTP healthcheck. Merge the PR with a merge commit. After main's own `quality` and `test` pass, the called production workflow reads that merge commit's development parent SHA, requires a successful development **CI run with a successful development EC2 deploy job** for that SHA, reads its ECR digest, and deploys that digest. There is no production build.
3. Each EC2 pulls that digest, copies the Compose definitions from that image into `/opt/traceback`, validates Compose, runs `migrate --noinput` against its own DB, then starts the new app with `docker compose up --wait`. The Compose healthcheck requests the allauth config endpoint; that endpoint also reads the DB. Migration failure prevents the app update. Existing app and DB schema may still be affected by a partially applied migration; review production migrations for backward compatibility and backup/rollback separately.
4. The healthcheck verifies the local container's HTTP/DB path. Reverse-proxy, TLS, external smoke, rollback and DB backup checks are still required for a production release. The SSM deploy script polls the command for up to ten minutes because the AWS CLI's default waiter can stop while pull or migration is still running.

Use a merge commit for `development → main`; fast-forward and squash releases do not satisfy the production workflow's source-SHA check. Protect `main` against direct pushes and require the PR checks; set the production Environment to require a human reviewer. Do not merge to main until that protection is active and the exact source SHA/digest and migration impact have been reviewed.

## Values to collect

Development values were verified in AWS account `968579693658` in the Seoul Region (`ap-northeast-2`). Private ECR repository `traceback` now exists in that account with immutable image tags and AES-256 encryption; it is empty until the first successful image push. Development and production must use this same account/Region/repository so production can promote the exact digest built for development. Retain promoted digests long enough for rollback; confirm lifecycle policy before enabling cleanup.

Use `.env.dev.git` and `.env.prod.git` as the GitHub Environment variable inventories. The `development` Environment now has four variables: `AWS_DEPLOY_ROLE_ARN`, `AWS_REGION`, `ECR_REPOSITORY`, and `DEVELOPMENT_INSTANCE_ID`. It is restricted to the `development` branch. There are no GitHub AWS access-key secrets or Docker Hub tokens. The `production` Environment is reserved for later; its role, values, `main` branch restriction, and required reviewer have not been configured. CI itself uses its own temporary Postgres DB and needs none of these environment values.

## GitHub OIDC provider and trust

The account's GitHub OIDC provider now exists at `https://token.actions.githubusercontent.com` with audience `sts.amazonaws.com`. Development role `traceback-development-deploy` now uses the trust policy below with `ENVIRONMENT=development` and account `968579693658`. Production role creation is deferred until production is being prepared. The template remains useful for that later role; replace `ENVIRONMENT` with exactly `production` and use the verified production account ID:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {"StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:orange-taco/traceback:environment:ENVIRONMENT"
    }}
  }]
}
```

The repository reports GitHub's default, non-immutable `sub` format (`use_default=true`, `use_immutable_subject=false`, checked 2026-10-03). Recheck it after repository transfer/rename: `gh api repos/orange-taco/traceback/actions/oidc/customization/sub`. Environment-based subjects do **not** encode a branch, so GitHub Environment branch restrictions and branch protection are essential. Do not broaden trust to all repositories or all environments.

## Deploy-role permission policy

Attach a distinct policy to each OIDC role. Substitute `REGION`, `ACCOUNT_ID`, `REPOSITORY`, and only the matching `INSTANCE_ID`. The development role includes the ECR push statement; a future production role must omit it. Both roles need the remaining statements. The `AWS-RunShellScript` document has an empty account component because it is AWS-owned.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid":"EcrAuth","Effect":"Allow","Action":"ecr:GetAuthorizationToken","Resource":"*"},
    {"Sid":"EcrRead","Effect":"Allow","Action":["ecr:DescribeRepositories","ecr:DescribeImages"],"Resource":"arn:aws:ecr:REGION:ACCOUNT_ID:repository/REPOSITORY"},
    {"Sid":"SsmDocument","Effect":"Allow","Action":"ssm:SendCommand","Resource":"arn:aws:ssm:REGION::document/AWS-RunShellScript"},
    {"Sid":"SsmTarget","Effect":"Allow","Action":"ssm:SendCommand","Resource":"arn:aws:ec2:REGION:ACCOUNT_ID:instance/INSTANCE_ID"},
    {"Sid":"SsmResult","Effect":"Allow","Action":"ssm:GetCommandInvocation","Resource":"*"}
  ]
}
```

The development role's inline policy includes this ECR push statement. A future production role must omit it:

```json
{"Sid":"EcrPush","Effect":"Allow","Action":["ecr:BatchCheckLayerAvailability","ecr:InitiateLayerUpload","ecr:UploadLayerPart","ecr:CompleteLayerUpload","ecr:PutImage","ecr:BatchGetImage"],"Resource":"arn:aws:ecr:REGION:ACCOUNT_ID:repository/REPOSITORY"}
```

`GetAuthorizationToken` and `GetCommandInvocation` cannot be restricted to a repository/command ARN with these APIs; all other actions above are resource-scoped. The production role does not push or mutate ECR. Neither role has EC2 administrative or IAM permissions. If an existing ECR repository policy denies these roles, align that policy without widening the role scope.

## Each EC2 instance profile and bootstrap

Attach `AmazonSSMManagedInstanceCore` to each app EC2 role. Add a repository-scoped pull policy, substituting its account/Region/repository:

```json
{
  "Version":"2012-10-17",
  "Statement":[
    {"Sid":"EcrAuth","Effect":"Allow","Action":"ecr:GetAuthorizationToken","Resource":"*"},
    {"Sid":"EcrPull","Effect":"Allow","Action":["ecr:BatchGetImage","ecr:GetDownloadUrlForLayer"],"Resource":"arn:aws:ecr:REGION:ACCOUNT_ID:repository/REPOSITORY"}
  ]
}
```

Check on **both** hosts: the EC2 architecture can run the GitHub-hosted runner's current `linux/amd64` image (otherwise decide on a multi-platform build separately); SSM Agent is online in the correct Region; outbound access to SSM, ECR API/registry and image storage works (internet/NAT or appropriate VPC endpoints); Docker Engine, Compose v2 and AWS CLI v2 are installed; the SSM command can invoke Docker; `/opt/traceback` exists; `/opt/traceback/.env` is root-owned, `chmod 600`, and contains server-specific values from the matching settings example (`config/server.development.env.example` or `config/server.env.example`). Set `DJANGO_SETTINGS_MODULE=config.settings.development` on the development host and `config.settings.production` on production. Keep separate DB URLs, Django keys, hostnames, frontend URLs and SES/Kakao credentials. Neither GitHub Environment variables nor the image contain runtime secrets. Confirm DB connectivity and backups before migration. Install Nginx on the EC2 host, obtain an HTTPS certificate for the API DNS name, and install `deploy/nginx/traceback.conf.example` after replacing its example hostname. The app listens only on `127.0.0.1:8000`; Nginx forwards HTTPS traffic to it. The security group should expose HTTP for ACME/redirect and HTTPS for Vercel, with no public app port.

The example Nginx file is not copied onto the host by `deploy-common.sh`; provision it
separately. It references certificate files, so serve the HTTP ACME challenge and
obtain the certificate before enabling that file. See the
[ordered HTTPS setup guide](artifact/2-dev-server-first-deployment.html#https-sequence).

Do not place passwords in SSM command parameters or GitHub logs. The SSM command does not print `.env`, but Compose/application error output could reveal sensitive data, so restrict access to command invocation output.

## Verification and release

### Completed development deployment setup (2026-10-03)

- GitHub `development` Environment allows only the `development` branch. Its four values match `.env.dev.git`; they are environment variables, not secrets. The `development` branch requires a pull request and the `Quality` and `Test` checks. Required approvals are set to zero to support the single-maintainer workflow; force pushes and branch deletion are disabled.
- AWS account `968579693658` has the GitHub OIDC provider and `traceback-development-deploy` role. Its trust subject is exactly `repo:orange-taco/traceback:environment:development`; its policy is limited to ECR repository `traceback` and SSM commands for EC2 `i-051f85a1ac4e64a2c`.
- Seoul private ECR repository `traceback` is immutable-tagged and AES-256 encrypted. It has no images yet.
- This setup has not been exercised by a `development` push workflow. The latest inspected CI run was a pull request, so deploy jobs were correctly skipped. It is not an OIDC deployment test.
- Still required before the first development push: grant the EC2 instance role ECR pull access, install Docker Engine/Compose v2/AWS CLI v2, prepare `/opt/traceback/.env`, create the Django DB user, and configure Nginx/TLS. Vercel's `DJANGO_ORIGIN` is active in the new deployment; end-to-end verification still requires API HTTPS and Django. The next deployment slice should start with the EC2 pull policy and host bootstrap.

Before the first development push, validate the `development` Environment and its four values; confirm OIDC trust/permissions, EC2 SSM online state, instance ECR pull permission, and ECR `IMMUTABLE` tags. Before production work, separately verify the `production` Environment, reviewer and branch restriction, production role/instance, and distinct database. Confirm environment IDs and each `.env` target match the intended account before deploying.

For development: push to `development` only after setup, observe the CI run's quality/test and deployment jobs, record the commit SHA and image digest, inspect SSM command success, then check the live endpoint, container image digest and DB migration state. A green CI job includes local container health but does not prove that the external reverse proxy and TLS path works.

For production: before approving the protected GitHub Environment deployment, present the development source SHA and exact ECR digest, migration operations, target production instance/DB and expected user impact. After the main merge and a fresh fetch, resolve the source SHA with `git rev-parse origin/main^2`; check that SHA's successful development `CI` push run with `gh run list --workflow ci.yml --branch development --event push --commit SHA --json databaseId,conclusion,url`, then confirm its `Deploy development EC2` job succeeded with `gh run view RUN_ID --json jobs`. Read the exact digest with `aws ecr describe-images --region REGION --repository-name REPOSITORY --image-ids imageTag=SHA --query 'imageDetails[0].imageDigest' --output text`. Substitute the actual SHA/Region/repository; do not approve if they disagree with the proposed release. After approval, compare the production container's image digest with the development digest and perform application/DB smoke checks. Do **not** run production deployment merely to test IAM or workflow wiring.

Re-running a development workflow for a commit with an existing immutable SHA tag reuses its digest and retries deployment; it does not rebuild or overwrite the image.

Secrets Manager is not part of this decision. Changing `/opt/traceback/.env` to another secret source requires a separate security/architecture review. The AWS/GitHub resource preparation checklist is in [`todo.md`](todo.md).
