# install-docker-admin.ps1
# Self-elevating Docker Desktop installer

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process pwsh -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -NoExit -File `"$PSCommandPath`""
    exit
}

Write-Host "Running as Administrator." -ForegroundColor Green

# Pre-create directory with correct ownership so installer doesn't complain
$dir = "C:\ProgramData\DockerDesktop"
if (Test-Path $dir) {
    Write-Host "Removing existing $dir ..."
    Remove-Item $dir -Recurse -Force
}
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$acl = Get-Acl $dir
$acl.SetOwner([System.Security.Principal.NTAccount]"BUILTIN\Administrators")
Set-Acl $dir $acl
icacls $dir /grant "Administrators:(OI)(CI)F" /grant "SYSTEM:(OI)(CI)F" /T | Out-Null
Write-Host "Directory ownership fixed." -ForegroundColor Green

$installer = "$env:TEMP\DockerDesktopInstaller.exe"
if (-not (Test-Path $installer)) {
    Write-Host "Installer not found: $installer" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Launching Docker Desktop installer..."
Start-Process $installer -Wait

Write-Host ""
Write-Host "Installer finished. Press any key to close..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
