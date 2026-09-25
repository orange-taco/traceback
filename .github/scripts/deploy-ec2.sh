#!/usr/bin/env bash
set -euo pipefail

: "${APP_IMAGE:?APP_IMAGE is required}"
: "${INSTANCE_ID:?INSTANCE_ID is required}"
: "${AWS_REGION:?AWS_REGION is required}"

if [[ ! "$APP_IMAGE" =~ ^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com/[A-Za-z0-9._/-]+@sha256:[0-9a-f]{64}$ ]]; then
  echo "APP_IMAGE must be an ECR image digest" >&2
  exit 1
fi

registry="${APP_IMAGE%%/*}"
commands_json="$(jq -nc \
  --arg image "$APP_IMAGE" \
  --arg region "$AWS_REGION" \
  --arg registry "$registry" '
  {commands: [
    "set -eu",
    "cd /opt/traceback",
    "docker compose version --short",
    ("aws ecr get-login-password --region " + $region + " | docker login --username AWS --password-stdin " + $registry),
    ("docker pull " + $image),
    ("docker run --rm --entrypoint cat " + $image + " /app/docker-compose.yml > docker-compose.yml.next"),
    ("docker run --rm --entrypoint cat " + $image + " /app/docker-compose_prod.yml > docker-compose_prod.yml.next"),
    "mv docker-compose.yml.next docker-compose.yml",
    "mv docker-compose_prod.yml.next docker-compose_prod.yml",
    ("APP_IMAGE=" + $image + " docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml config --quiet"),
    ("APP_IMAGE=" + $image + " docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml run --rm app python manage.py migrate --noinput"),
    ("APP_IMAGE=" + $image + " docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml up -d --no-build --wait app")
  ]}')"

command_id="$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "$commands_json" \
  --query 'Command.CommandId' \
  --output text)"

# The AWS CLI waiter stops after about 100 seconds, which can be shorter than
# the image pull and migration. Poll for up to ten minutes instead.
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
