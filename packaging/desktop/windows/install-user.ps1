param([string]$Binary = (Join-Path $PSScriptRoot 'findrail-desktop.exe'))
$ErrorActionPreference = 'Stop'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Programs')) 'Findrail.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = (Resolve-Path $Binary).Path
$shortcut.WorkingDirectory = Split-Path -Parent (Resolve-Path $Binary).Path
$shortcut.Save()
Write-Output "Installed user shortcut: $shortcutPath"
