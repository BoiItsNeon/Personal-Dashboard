$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Launcher = Join-Path $ProjectDir "start_dashboard.ps1"
$StartupFolder = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupFolder "News and Market Dashboard.lnk"

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher script was not found at $Launcher."
    exit 1
}

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Launcher`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.IconLocation = "powershell.exe,0"
$Shortcut.Description = "Starts the News and Market Dashboard on Windows sign-in."
$Shortcut.Save()

Write-Host "Startup shortcut created:"
Write-Host $ShortcutPath
