$WshShell = New-Object -ComObject WScript.Shell
$StartMenuPath = [IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs")
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$BatPath = Join-Path $PSScriptRoot "start_computer_agent.bat"

# Create Start Menu Shortcut
$StartMenuLink = Join-Path $StartMenuPath "Computer Agent.lnk"
$Shortcut = $WshShell.CreateShortcut($StartMenuLink)
$Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
$Shortcut.Arguments = "/c `"$BatPath`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = "shell32.dll, 43"
$Shortcut.Save()

# Create Desktop Shortcut
$DesktopLink = Join-Path $DesktopPath "Computer Agent.lnk"
$Shortcut = $WshShell.CreateShortcut($DesktopLink)
$Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
$Shortcut.Arguments = "/c `"$BatPath`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = "shell32.dll, 43"
$Shortcut.Save()

Write-Host "Shortcuts created in Start Menu and on Desktop."
Write-Host "If Voice Access still cannot find it, say 'Search for Computer Agent' or create a custom voice shortcut."
