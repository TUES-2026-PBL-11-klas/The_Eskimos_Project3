<#
Windows task runner — PowerShell equivalent of the Makefile, for hosts without GNU make.
Usage:  .\tasks.ps1 <target>
        .\tasks.ps1 build | up | down | migrate | seed | run | clean-events | lint | fmt |
                    test | test-unit | test-integration
Everything runs in Docker — no local venv or Postgres required. Mirrors the Makefile 1:1.
#>
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('build', 'up', 'down', 'migrate', 'seed', 'run', 'clean-events', 'lint', 'fmt',
                 'test', 'test-unit', 'test-integration')]
    [string]$Target
)

$ErrorActionPreference = 'Stop'

switch ($Target) {
    'build'            { docker compose --profile jobs --profile dev build }
    'up'               { docker compose up -d postgres }
    'down'             { docker compose down -v }
    'migrate'          { docker compose run --rm ingestion alembic upgrade head }
    'seed'             { docker compose run --rm ingestion python -m ingestion.db.seed }
    'run'              { docker compose run --rm ingestion }
    'clean-events'     { docker compose run --rm cleanup }
    'lint'             { docker compose run --rm test sh -c "ruff check . && mypy src" }
    'fmt'              { docker compose run --rm test ruff format . }
    'test'             { docker compose run --rm test }
    'test-unit'        { docker compose run --rm test pytest -m unit }
    'test-integration' { docker compose run --rm test pytest -m integration }
}
