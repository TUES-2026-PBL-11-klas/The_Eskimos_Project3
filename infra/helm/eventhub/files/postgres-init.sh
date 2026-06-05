#!/bin/bash
# Runs once, on first cluster initialization (mounted into docker-entrypoint-initdb.d via the
# postgres-init ConfigMap). The postgres entrypoint provides POSTGRES_USER / POSTGRES_DB and the
# extra env the StatefulSet injects (USERS_DB, API_READER_PASSWORD). Identifiers below are the
# chart's own controlled values, so they are interpolated directly; the password is passed as a
# psql variable (:'reader_pw') so it is quoted safely regardless of its contents.
set -euo pipefail

# api_reader: the read-only login the API uses against the events DB. Granted SELECT on existing
# tables and, via ALTER DEFAULT PRIVILEGES, on tables the ingestion migrations create later.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v reader_pw="$API_READER_PASSWORD" <<SQL
CREATE ROLE api_reader WITH LOGIN PASSWORD :'reader_pw';
GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO api_reader;
GRANT USAGE ON SCHEMA public TO api_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO api_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO api_reader;
SQL

# Separate database for user accounts (decision D4: one instance, two DBs), owned by the app role.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE DATABASE "$USERS_DB" OWNER "$POSTGRES_USER";
SQL
