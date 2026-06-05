#!/usr/bin/env bash
# Turn the real EventHub secret values into committable SealedSecrets.
# Run AFTER the cluster + Sealed Secrets controller exist (Deploy Plan gate 9). Needs `kubectl`
# and `kubeseal` on PATH and a kubeconfig pointing at the cluster. Plain values are read from
# prompts and never written to disk — only the encrypted sealed-*.yaml are.
set -euo pipefail

NAMESPACE="${NAMESPACE:-eventhub}"
PGHOST="${PGHOST:-eventhub-postgres}"
EVENTS_DB="${EVENTS_DB:-eventhub}"
USERS_DB="${USERS_DB:-eventhub_users}"
OUT_DIR="${OUT_DIR:-"$(dirname "$0")/sealed"}"

# Use the value from infra/.env when exported; otherwise prompt.
PG_PASSWORD="${EVENTHUB_PG_PASSWORD:-}"
[ -n "$PG_PASSWORD" ] || { read -rsp "Postgres superuser/app (eventhub) password: " PG_PASSWORD; echo; }
READER_PW="${EVENTHUB_API_READER_PASSWORD:-}"
[ -n "$READER_PW" ] || { read -rsp "API read-login (api_reader) password: " READER_PW; echo; }
DISCORD="${EVENTHUB_DISCORD_WEBHOOK:-}"
[ -n "$DISCORD" ] || { read -rsp "Discord webhook URL: " DISCORD; echo; }
GHCR_USER="${EVENTHUB_GHCR_USER:-}"
[ -n "$GHCR_USER" ] || read -rp "GHCR username (your GitHub user/org): " GHCR_USER
GHCR_TOKEN="${EVENTHUB_GHCR_TOKEN:-}"
[ -n "$GHCR_TOKEN" ] || { read -rsp "GHCR token (classic PAT, read:packages): " GHCR_TOKEN; echo; }

INGESTION_URL="postgresql+asyncpg://eventhub:${PG_PASSWORD}@${PGHOST}:5432/${EVENTS_DB}"
EVENTS_URL="postgresql+asyncpg://api_reader:${READER_PW}@${PGHOST}:5432/${EVENTS_DB}"
USERS_URL="postgresql+asyncpg://eventhub:${PG_PASSWORD}@${PGHOST}:5432/${USERS_DB}"

mkdir -p "$OUT_DIR"

echo "Sealing into $OUT_DIR ..."

kubectl create secret generic eventhub-db --namespace "$NAMESPACE" --dry-run=client -o yaml \
  --from-literal=POSTGRES_PASSWORD="$PG_PASSWORD" \
  --from-literal=API_READER_PASSWORD="$READER_PW" \
  --from-literal=INGESTION_DATABASE_URL="$INGESTION_URL" \
  --from-literal=EVENTS_DB_URL="$EVENTS_URL" \
  --from-literal=USERS_DB_URL="$USERS_URL" \
  | kubeseal --format yaml > "$OUT_DIR/sealed-db.yaml"
echo "  wrote sealed-db.yaml"

kubectl create secret generic eventhub-alerts --namespace "$NAMESPACE" --dry-run=client -o yaml \
  --from-literal=discord-webhook-url="$DISCORD" \
  | kubeseal --format yaml > "$OUT_DIR/sealed-alerts.yaml"
echo "  wrote sealed-alerts.yaml"

kubectl create secret docker-registry ghcr-pull --namespace "$NAMESPACE" --dry-run=client -o yaml \
  --docker-server=ghcr.io --docker-username="$GHCR_USER" --docker-password="$GHCR_TOKEN" \
  | kubeseal --format yaml > "$OUT_DIR/sealed-ghcr.yaml"
echo "  wrote sealed-ghcr.yaml"

echo "Done. Review, then: git add $OUT_DIR/sealed-*.yaml && commit."
