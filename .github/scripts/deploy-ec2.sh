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
    ("APP_IMAGE=" + $image + " docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml pull app"),
    ("APP_IMAGE=" + $image + " docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml run --rm app python manage.py migrate --noinput"),
    ("APP_IMAGE=" + $image + " docker compose --env-file .env -f docker-compose.yml -f docker-compose_prod.yml up -d --no-build --wait app")
  ]}')"

command_id="$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "$commands_json" \
  --query 'Command.CommandId' \
  --output text)"

if ! aws ssm wait command-executed \
  --command-id "$command_id" \
  --instance-id "$INSTANCE_ID"; then
  aws ssm get-command-invocation \
    --command-id "$command_id" \
    --instance-id "$INSTANCE_ID" || true
  exit 1
fi

aws ssm get-command-invocation \
  --command-id "$command_id" \
  --instance-id "$INSTANCE_ID"
