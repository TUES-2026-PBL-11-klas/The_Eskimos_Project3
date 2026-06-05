<#
.SYNOPSIS
  Load infra/.env into the current PowerShell session as environment variables.

.DESCRIPTION
  Dot-source it so the variables persist in your shell:
      cd infra
      . ./load-env.ps1
  After loading, `terraform` sees TF_VAR_*/AWS_* and `k8s/seal.ps1` sees the EVENTHUB_* values.
#>
[CmdletBinding()]
param(
  [string]$Path
)

if (-not $Path) {
  $base = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
  $Path = Join-Path $base ".env"
}

if (-not (Test-Path $Path)) {
  Write-Error "No '$Path' found. Copy .env.example to .env and fill it in."
  return
}

$count = 0
Get-Content $Path | ForEach-Object {
  $line = $_.Trim()
  if ($line -eq "" -or $line.StartsWith("#")) { return }
  $idx = $line.IndexOf("=")
  if ($idx -lt 1) { return }
  $name = $line.Substring(0, $idx).Trim()
  $value = $line.Substring($idx + 1)
  # Strip an inline comment (whitespace then '#'), so trailing "# note" never leaks into a value.
  $value = [regex]::Replace($value, '\s+#.*$', '')
  $value = $value.Trim().Trim('"')
  # Always set (even empty) so a re-run overwrites/clears any stale value from a previous load.
  [Environment]::SetEnvironmentVariable($name, $value, [System.EnvironmentVariableTarget]::Process)
  if ($value -ne "") { $count++ }
}

Write-Host "Loaded $count variable(s) from $Path into this session." -ForegroundColor Green
