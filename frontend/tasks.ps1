# EventHub frontend task runner (Windows / PowerShell).
# 1:1 mirror of the Makefile (Linux/macOS). Keep both in sync.
#
# Usage: .\tasks.ps1 <target>
#   install dev build lint fmt typecheck gen-api docker-build up down

param(
    [Parameter(Position = 0)]
    [string]$Task = "help"
)

$ErrorActionPreference = "Stop"

switch ($Task) {
    "install"      { npm install }
    "dev"          { npm run dev }
    "build"        { npm run build }
    "lint"         { npm run lint }
    "fmt"          { npm run fmt }
    "typecheck"    { npm run typecheck }
    # Regenerate lib/api/schema.d.ts from the live API's /openapi.json (API must be up).
    "gen-api"      { npm run gen-api }
    "docker-build" { docker build -t eventhub-frontend . }
    # Build + run the frontend container in the background (isolated, mock data).
    "up"           { docker compose up --build -d }
    "down"         { docker compose down }
    default {
        Write-Host "Targets: install dev build lint fmt typecheck gen-api docker-build up down"
    }
}
