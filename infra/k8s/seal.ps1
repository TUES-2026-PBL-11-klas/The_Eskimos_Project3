<#
.SYNOPSIS
  Turn the real EventHub secret values into committable SealedSecrets.

.DESCRIPTION
  Run AFTER the cluster and the Sealed Secrets controller exist (Deploy Plan gate 9). Requires
  `kubectl` and `kubeseal` on PATH and a kubeconfig pointing at the cluster. Plain values are read
  from prompts (or env vars) and never written to disk — only the encrypted sealed-*.yaml are.

.EXAMPLE
  ./seal.ps1
#>
[CmdletBinding()]
param(
  [string]$Namespace = "eventhub",
  [string]$PgHost    = "eventhub-postgres",
  [string]$EventsDb  = "eventhub",
  [string]$UsersDb   = "eventhub_users",
  [string]$OutDir    = "$PSScriptRoot/sealed"
)

$ErrorActionPreference = "Stop"

function Read-Secret([string]$Prompt) {
  $secure = Read-Host -AsSecureString $Prompt
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

# Use the value from infra/.env (loaded via load-env.ps1) when present; otherwise prompt.
function Get-Secret([string]$EnvName, [string]$Prompt) {
  $existing = [Environment]::GetEnvironmentVariable($EnvName)
  if (-not [string]::IsNullOrEmpty($existing)) { return $existing }
  return Read-Secret $Prompt
}
function Get-Plain([string]$EnvName, [string]$Prompt) {
  $existing = [Environment]::GetEnvironmentVariable($EnvName)
  if (-not [string]::IsNullOrEmpty($existing)) { return $existing }
  return Read-Host $Prompt
}

# --- collect plain values (env from infra/.env, else prompt) ---
$pgPassword   = Get-Secret "EVENTHUB_PG_PASSWORD"         "Postgres superuser/app (eventhub) password"
$readerPw     = Get-Secret "EVENTHUB_API_READER_PASSWORD" "API read-login (api_reader) password"
$discord      = Get-Secret "EVENTHUB_DISCORD_WEBHOOK"     "Discord webhook URL"
$ghcrUser     = Get-Plain  "EVENTHUB_GHCR_USER"           "GHCR username (your GitHub user/org)"
$ghcrToken    = Get-Secret "EVENTHUB_GHCR_TOKEN"          "GHCR token (classic PAT, read:packages)"

$ingestionUrl = "postgresql+asyncpg://eventhub:$pgPassword@${PgHost}:5432/$EventsDb"
$eventsUrl    = "postgresql+asyncpg://api_reader:$readerPw@${PgHost}:5432/$EventsDb"
$usersUrl     = "postgresql+asyncpg://eventhub:$pgPassword@${PgHost}:5432/$UsersDb"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

function Seal-Generic([string]$Name, [hashtable]$Literals, [string]$OutFile) {
  $args = @("create", "secret", "generic", $Name, "--namespace", $Namespace,
            "--dry-run=client", "-o", "yaml")
  foreach ($k in $Literals.Keys) { $args += "--from-literal=$k=$($Literals[$k])" }
  kubectl @args | kubeseal --format yaml | Out-File -Encoding ascii "$OutDir/$OutFile"
  Write-Host "  wrote $OutFile"
}

Write-Host "Sealing into $OutDir ..."

Seal-Generic -Name "eventhub-db" -OutFile "sealed-db.yaml" -Literals @{
  POSTGRES_PASSWORD      = $pgPassword
  API_READER_PASSWORD    = $readerPw
  INGESTION_DATABASE_URL = $ingestionUrl
  EVENTS_DB_URL          = $eventsUrl
  USERS_DB_URL           = $usersUrl
}

Seal-Generic -Name "eventhub-alerts" -OutFile "sealed-alerts.yaml" -Literals @{
  "discord-webhook-url" = $discord
}

kubectl create secret docker-registry ghcr-pull `
  --namespace $Namespace --docker-server=ghcr.io `
  --docker-username=$ghcrUser --docker-password=$ghcrToken `
  --dry-run=client -o yaml | kubeseal --format yaml | Out-File -Encoding ascii "$OutDir/sealed-ghcr.yaml"
Write-Host "  wrote sealed-ghcr.yaml"

Write-Host "Done. Review, then: git add $OutDir/sealed-*.yaml && commit."
