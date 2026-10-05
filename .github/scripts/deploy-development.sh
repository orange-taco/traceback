#!/usr/bin/env bash
set -euo pipefail

: "${DEVELOPMENT_INSTANCE_ID:?DEVELOPMENT_INSTANCE_ID is required}"
export DEPLOY_INSTANCE_ID="$DEVELOPMENT_INSTANCE_ID"

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$script_dir/deploy-common.sh"
