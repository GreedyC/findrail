$ErrorActionPreference = 'Stop'
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Programs')) 'Findrail.lnk'
Remove-Item -LiteralPath $shortcutPath -Force -ErrorAction SilentlyContinue
Write-Output 'Removed Findrail shortcut. User data was not changed.'
