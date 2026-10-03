#!/usr/bin/env bash
set -euo pipefail

# Validate the image and deployment target before making an AWS request.
: "${APP_IMAGE:?APP_IMAGE is required}"
: "${INSTANCE_ID:?INSTANCE_ID is required}"
: "${AWS_REGION:?AWS_REGION is required}"

if [[ ! "$INSTANCE_ID" =~ ^i-[0-9a-f]+$ ]]; then
  echo "INSTANCE_ID must be an EC2 instance ID" >&2
  exit 1
fi

if [[ ! "$AWS_REGION" =~ ^[a-z0-9-]+$ ]]; then
  echo "AWS_REGION contains unsupported characters" >&2
  exit 1
fi

if [[ ! "$APP_IMAGE" =~ ^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[A-Za-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]; then
  echo "APP_IMAGE must be an ECR image digest" >&2
  exit 1
fi

registry="${APP_IMAGE%%/*}"
# SSM Run Command accepts one JSON object containing the EC2 shell commands.
commands=(
  "set -eu"
  "cd /opt/traceback"
  "docker compose version --short"
  "aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $registry"
  "docker pull $APP_IMAGE"
  "docker run --rm --entrypoint cat $APP_IMAGE /app/docker-compose.yml > docker-compose.yml.next"
  "docker run --rm --entrypoint cat $APP_IMAGE /app/docker-compose_prod.yml > docker-compose_prod.yml.next"
  "mv docker-compose.yml.next docker-compose.yml"
  "mv docker-compose_prod.yml.next docker-compose_prod.yml"
  "APP_IMAGE=$APP_IMAGE docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml config --quiet"
  "APP_IMAGE=$APP_IMAGE docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml run --rm app python manage.py migrate --noinput"
  "APP_IMAGE=$APP_IMAGE docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml up -d --no-build --wait app"
)
commands_json="$(jq -nc --args '$ARGS.positional | {commands: .}' -- "${commands[@]}")"

# Send the deployment sequence to EC2 through SSM; no SSH session is opened.
command_id="$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "$commands_json" \
  --query 'Command.CommandId' \
  --output text)"

# Poll longer than the default AWS CLI waiter because image pulls and migrations
# may take more than 100 seconds on a small development instance.
status=Pending
for ((attempt = 0; attempt < 120; attempt++)); do
  status="$(aws ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$INSTANCE_ID" \
    --query Status --output text 2>/dev/null || true)"
  case "$status" in
    Success|Failed|Cancelled|TimedOut) break ;;
  esac
  sleep 5
done

aws ssm get-command-invocation \
  --command-id "$command_id" \
  --instance-id "$INSTANCE_ID"
test "$status" = Success
