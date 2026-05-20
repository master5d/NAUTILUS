$ShortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\HermesAutoStart.lnk"
$ScriptPath = "C:\telo\Atlas\Scripts\hermes_startup.ps1"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$ScriptPath`""
$Shortcut.WindowStyle = 7 # Minimized
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Save()
Write-Host "Auto-start shortcut created in Windows Startup folder."
