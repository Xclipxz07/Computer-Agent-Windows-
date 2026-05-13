$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\Claire 2.0.lnk")
# Use cmd.exe as the target to enable pinning to taskbar
$BatPath = "$PSScriptRoot\start_claire.bat"
$Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
$Shortcut.Arguments = "/c `"$BatPath`""
$Shortcut.WorkingDirectory = "$PSScriptRoot"
$Shortcut.WindowStyle = 1
$Shortcut.Description = "Start Claire 2.0 Voice Assistant"
# Set a nice icon (Yellow Star from shell32.dll)
$Shortcut.IconLocation = "shell32.dll, 43" 
$Shortcut.Save()

Write-Host "Desktop shortcut created successfully!"
