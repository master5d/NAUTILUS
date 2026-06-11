# swarm.ps1 — dispatch a task to the active SOVERN orchestrator agent (headless).
# Usage:
#   swarm "опиши архитектуру NAUTILUS"        → запускает через активного агента
#   swarm -List                                → показать агентов и кто активен
#   swarm -Switch codex                        → переключить активного агента
#   swarm -Agent hermes "задача"               → one-off через конкретного агента
# Active agent lives in config/orchestrator.json; dashboard (:4002) switches it too.

[CmdletBinding(DefaultParameterSetName = 'Run')]
param(
    [Parameter(ParameterSetName = 'Run', Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Task,

    [Parameter(ParameterSetName = 'Run')]
    [string]$Agent,

    [Parameter(ParameterSetName = 'List')]
    [switch]$List,

    [Parameter(ParameterSetName = 'Switch', Mandatory = $true)]
    [string]$Switch
)

$ErrorActionPreference = 'Stop'
$orchPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'config\orchestrator.json'
$orch = Get-Content $orchPath -Raw | ConvertFrom-Json

if ($List) {
    Write-Host "Активный оркестратор: $($orch.active)" -ForegroundColor Cyan
    foreach ($p in $orch.agents.PSObject.Properties) {
        $mark = if ($p.Name -eq $orch.active) { '👑' } else { '  ' }
        Write-Host ("{0} {1,-12} {2}" -f $mark, $p.Name, $p.Value.notes)
    }
    return
}

if ($PSCmdlet.ParameterSetName -eq 'Switch') {
    if (-not $orch.agents.PSObject.Properties[$Switch]) {
        Write-Error "Неизвестный агент '$Switch'. Доступны: $($orch.agents.PSObject.Properties.Name -join ', ')"
    }
    $orch.active = $Switch
    $orch.updated = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $tmp = "$orchPath.tmp"
    $orch | ConvertTo-Json -Depth 5 | Set-Content $tmp -Encoding utf8NoBOM
    Move-Item $tmp $orchPath -Force
    Write-Host "👑 Оркестратор переключён на: $Switch" -ForegroundColor Green
    return
}

if (-not $Task) {
    Write-Host 'Usage: swarm "задача"  |  swarm -List  |  swarm -Switch <agent>' -ForegroundColor Yellow
    return
}

$name = if ($Agent) { $Agent } else { $orch.active }
$def = $orch.agents.PSObject.Properties[$name]
if (-not $def) {
    Write-Error "Неизвестный агент '$name'. Доступны: $($orch.agents.PSObject.Properties.Name -join ', ')"
}
$def = $def.Value

# Native invocation — args идут массивом без шелл-интерполяции (нет cmd /c,
# нет injection через & | % "). {task} подставляется строковым Replace —
# никакой regex-магии с $-подстановками.
$taskText = $Task -join ' '
$argv = @($def.args | ForEach-Object { $_.Replace('{task}', $taskText) })

Write-Host "🚀 [$name] $($def.exe) $($argv -join ' ')" -ForegroundColor DarkGray
Push-Location $def.cwd
try {
    # $null | — закрывает stdin (headless CLI вроде codex иначе виснут)
    $null | & $def.exe @argv
    if ($LASTEXITCODE -ne 0) { Write-Warning "[$name] exited with code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
