# AWS deployment setup (manual, before first deployment)

This runbook covers the confirmed GitHub-hosted runner → OIDC → ECR/SSM → separate EC2/DB path. No AWS resource is created by this repository. Infrastructure creation, production deployment, and any change with a cost require the owner's separate approval.

## Current delivery contract

1. `development` push runs `quality` and `test` in `ci.yml`. Both must pass before the called development workflow builds a production-target image, tags it with the development commit SHA, pushes it to ECR, and deploys its **digest** through SSM.
2. A `development → main` PR runs the production-container smoke test within `quality`: it starts the built image, migrates a temporary SQLite database and waits for its HTTP healthcheck. After main's own `quality` and `test` pass, the called production workflow finds the merge-base development SHA, requires a successful development **CI run with a successful development EC2 deploy job** for that SHA, reads its ECR digest, and deploys that digest. There is no production build.
3. Each EC2 pulls that digest, copies the Compose definitions from that image into `/opt/traceback`, validates Compose, runs `migrate --noinput` against its own DB, then starts the new app with `docker compose up --wait`. The Compose healthcheck requests the allauth config endpoint; that endpoint also reads the DB. Migration failure prevents the app update. Existing app and DB schema may still be affected by a partially applied migration; review production migrations for backward compatibility and backup/rollback separately.
4. The healthcheck verifies the local container's HTTP/DB path. Reverse-proxy, TLS, external smoke, rollback and DB backup checks are still required for a production release. The SSM deploy script polls the command for up to ten minutes because the AWS CLI's default waiter can stop while pull or migration is still running.

Do not squash the `development → main` merge: the development commit must remain in `main` history. Protect `main` against direct pushes and require the PR checks; set the production Environment to require a human reviewer. Do not merge to main until that protection is active and the exact source SHA/digest and migration impact have been reviewed.

## Values to collect

The target AWS account ID, Region, repository, and instance IDs must be verified in the intended account before entering them. Existing templates use Region `ap-northeast-2`, ECR repository `traceback`, and GitHub repository `orange-taco/traceback`; these are **not** evidence that the resources exist. ECR must be a private repository in one account/Region for both environments, with image-tag immutability enabled so a successful development SHA cannot later point at another digest. Retain promoted digests long enough for rollback; confirm lifecycle policy before enabling cleanup.

Use `.env.dev.git` and `.env.prod.git` as the exact GitHub Environment variable inventories. There are no GitHub AWS access-key secrets or Docker Hub tokens. `AWS_DEPLOY_ROLE_ARN` is the relevant environment's OIDC deployment role. `AWS_REGION` and `ECR_REPOSITORY` must match across environments; instance IDs must differ. Restrict the `development` Environment to `development` branch, and `production` to `main` branch. Production requires a reviewer; disable self-review prevention only if a sole-maintainer approval is intended. CI itself uses its own temporary Postgres DB and needs none of these environment values.

## GitHub OIDC provider and trust

Create the account's GitHub OIDC provider with URL `https://token.actions.githubusercontent.com` and audience `sts.amazonaws.com` if it does not already exist. Use two roles: `traceback-development-deploy` and `traceback-production-deploy`. The trust policy for each is the following, replacing `ENVIRONMENT` with **exactly** `development` or `production` and `ACCOUNT_ID` with the target account ID:

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

The repository currently reports GitHub's default, non-immutable `sub` format (`use_default=true`, `use_immutable_subject=false`, checked 2026-09-25). Recheck it before creating roles or after repository transfer/rename: `gh api repos/orange-taco/traceback/actions/oidc/customization/sub`. Environment-based subjects do **not** encode a branch, so GitHub Environment branch restrictions and branch protection are essential. Do not broaden trust to all repositories or all environments.

## Deploy-role permission policy

Attach a distinct policy to each OIDC role. Substitute `REGION`, `ACCOUNT_ID`, `REPOSITORY`, and only the matching `INSTANCE_ID`. For development, include the ECR push statement; for production, omit it. Both need the remaining statements. The `AWS-RunShellScript` document has an empty account component because it is AWS-owned.

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

Add this statement to the **development role only**:

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

Check on **both** hosts: the EC2 architecture can run the GitHub-hosted runner's current `linux/amd64` image (otherwise decide on a multi-platform build separately); SSM Agent is online in the correct Region; outbound access to SSM, ECR API/registry and image storage works (internet/NAT or appropriate VPC endpoints); Docker Engine, Compose v2 and AWS CLI v2 are installed; the SSM command can invoke Docker; `/opt/traceback` exists; `/opt/traceback/.env` is root-owned, `chmod 600`, and contains server-specific values from `config/server.env.example`. Set `DJANGO_SETTINGS_MODULE=config.settings.development` on the development host and `config.settings.production` on production. Keep separate DB URLs, Django keys, hostnames, frontend URLs and SES/Kakao credentials. Neither GitHub Environment variables nor the image contain runtime secrets. Confirm DB connectivity and backups before migration. Configure a reverse proxy/TLS and a private or appropriately restricted app network path separately; Compose publishes no app host port in the production overlay.

Do not place passwords in SSM command parameters or GitHub logs. The SSM command does not print `.env`, but Compose/application error output could reveal sensitive data, so restrict access to command invocation output.

## Verification and release

Before the first merge, validate `gh api repos/orange-taco/traceback/environments` and the four values in **each** environment (do not print secrets); confirm OIDC trust/permissions and instance SSM online state in the intended AWS account. Verify the ECR repository has `IMMUTABLE` tags. Confirm both instance IDs point to separate app EC2s and their `.env` files target separate DBs.

For development: push to `development` only after setup, observe the CI run's quality/test and deployment jobs, record the commit SHA and image digest, inspect SSM command success, then check the live endpoint, container image digest and DB migration state. A green CI job includes local container health but does not prove that the external reverse proxy and TLS path works.

For production: before approving the protected GitHub Environment deployment, present the development source SHA and exact ECR digest, migration operations, target production instance/DB and expected user impact. After the main merge and a fresh fetch, resolve `git merge-base origin/main origin/development`; check that SHA's successful development `CI` push run with `gh run list --workflow ci.yml --branch development --event push --commit SHA --json databaseId,conclusion,url`, then confirm its `Deploy development EC2` job succeeded with `gh run view RUN_ID --json jobs`. Read the exact digest with `aws ecr describe-images --region REGION --repository-name REPOSITORY --image-ids imageTag=SHA --query 'imageDetails[0].imageDigest' --output text`. Substitute the actual SHA/Region/repository; do not approve if they disagree with the proposed release. After approval, compare the production container's image digest with the development digest and perform application/DB smoke checks. Do **not** run production deployment merely to test IAM or workflow wiring.

Re-running a development workflow for a commit with an existing immutable SHA tag reuses its digest and retries deployment; it does not rebuild or overwrite the image.

Secrets Manager is not part of this decision. Changing `/opt/traceback/.env` to another secret source requires a separate security/architecture review. The AWS/GitHub resource preparation checklist is in [`todo.md`](todo.md).
