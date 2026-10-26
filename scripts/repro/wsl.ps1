$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).ProviderPath
$scriptName = if ($args.Count -gt 0) { [string]$args[0] } else { 'serve_small.sh' }
[string[]]$forwardArgs = @()
if ($args.Count -gt 1) {
    $forwardArgs = @($args | Select-Object -Skip 1)
}
if ([IO.Path]::GetFileName($scriptName) -ne $scriptName -or -not $scriptName.EndsWith('.sh')) {
    throw 'Pass the name of a shell script in scripts/repro.'
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $scriptName))) {
    throw "Unknown reproduction script: $scriptName"
}
& wsl -d Ubuntu -u root --cd $workspaceRoot -- bash scripts/repro/mount_workspace.sh
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& wsl -d Ubuntu --cd /mnt/agentkv-newAgentKV -- bash "scripts/repro/$scriptName" @forwardArgs
exit $LASTEXITCODE
