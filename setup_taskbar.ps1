$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Computer Agent.lnk"

if (-not (Test-Path $ShortcutPath)) {
    Write-Host "Desktop shortcut not found. Creating it first..."
    $BatPath = Join-Path $PSScriptRoot "start_computer_agent.bat"
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
    $Shortcut.Arguments = "/c `"$BatPath`""
    $Shortcut.WorkingDirectory = $PSScriptRoot
    $Shortcut.IconLocation = "shell32.dll, 43" # Yellow Star icon
    $Shortcut.Save()
}

Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show("To pin Computer Agent to your Taskbar:`n`n1. Right-click the 'Computer Agent' shortcut on your Desktop.`n2. Select 'Pin to taskbar' (or 'Show more options' > 'Pin to taskbar' on Windows 11).", "Pin to Taskbar")

# Highlight the shortcut in Explorer
explorer /select,$ShortcutPath
