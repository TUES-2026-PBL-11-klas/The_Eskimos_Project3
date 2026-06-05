<#
Windows task runner — PowerShell equivalent of the Makefile, for hosts without GNU make.
Usage:  .\tasks.ps1 <target>
        .\tasks.ps1 build | up | down | migrate | seed | run | lint | fmt |
                    test | test-unit | test-integration
Everything runs in Docker — no local venv or Postgres required. Mirrors the Makefile 1:1.
The events DB is the ingestion service's Postgres: start it first from `ingestion/` with
`.\tasks.ps1 up` (it exposes port 5432 on the host).
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('build', 'up', 'down', 'migrate', 'seed', 'run', 'lint', 'fmt',
                 'test', 'test-unit', 'test-integration')]
    [string]$Target
)

$ErrorActionPreference = 'Stop'

switch ($Target) {
    'build'            { docker compose --profile dev build }
    'up'               { docker compose up -d api }
    'down'             { docker compose down -v }
    'migrate'          { docker compose run --rm api alembic upgrade head }
    'seed'             { docker compose run --rm test python -m api.db.seed_events }
    'run'              { docker compose up api }
    'lint'             { docker compose run --rm test sh -c "ruff check . && mypy src" }
    'fmt'              { docker compose run --rm test ruff format . }
    'test'             { docker compose run --rm test }
    'test-unit'        { docker compose run --rm test pytest -m unit }
    'test-integration' { docker compose run --rm test pytest -m integration }
}
