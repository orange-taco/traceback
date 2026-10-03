#!/usr/bin/env bash
set -euo pipefail

: "${APP_IMAGE:?APP_IMAGE is required}"
: "${DEPLOY_INSTANCE_ID:?DEPLOY_INSTANCE_ID is required}"
: "${AWS_REGION:?AWS_REGION is required}"

if [[ ! "$DEPLOY_INSTANCE_ID" =~ ^i-[0-9a-f]+$ ]]; then
  echo "DEPLOY_INSTANCE_ID must be an EC2 instance ID" >&2
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

command_id="$(aws ssm send-command \
  --instance-ids "$DEPLOY_INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "$commands_json" \
  --query 'Command.CommandId' \
  --output text)"

# The default AWS CLI waiter can stop before a small instance finishes pulling
# the image and applying migrations. Poll for up to ten minutes instead.
status=Pending
for ((attempt = 0; attempt < 120; attempt++)); do
  if invocation="$(aws ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$DEPLOY_INSTANCE_ID" \
    --query Status --output text 2>&1)"; then
    status="$invocation"
  elif [[ "$invocation" == *InvocationDoesNotExist* ]]; then
    # SendCommand can become visible shortly after it returns its command ID.
    status=Pending
  else
    printf '%s\n' "$invocation" >&2
    exit 1
  fi
  case "$status" in
    Success|Failed|Cancelled|TimedOut) break ;;
  esac
  sleep 5
done

aws ssm get-command-invocation \
  --command-id "$command_id" \
  --instance-id "$DEPLOY_INSTANCE_ID"
test "$status" = Success
