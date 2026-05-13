$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Claire 2.0.lnk"

if (-not (Test-Path $ShortcutPath)) {
    Write-Host "Desktop shortcut not found. Creating it first..."
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    # Use cmd.exe as target to enable pinning
    $BatPath = "$PSScriptRoot\start_claire.bat"
    $Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
    $Shortcut.Arguments = "/c `"$BatPath`""
    $Shortcut.WorkingDirectory = "$PSScriptRoot"
    $Shortcut.IconLocation = "shell32.dll, 43" # Yellow Star icon
    $Shortcut.Save()
}
else {
    # Update existing shortcut to ensure it's pinnable
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $BatPath = "$PSScriptRoot\start_claire.bat"
    $Shortcut.TargetPath = "C:\Windows\System32\cmd.exe"
    $Shortcut.Arguments = "/c `"$BatPath`""
    $Shortcut.WorkingDirectory = "$PSScriptRoot"
    $Shortcut.IconLocation = "shell32.dll, 43"
    $Shortcut.Save()
}

Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show("To pin Claire 2.0 to your Taskbar:`n`n1. Right-click the 'Claire 2.0' shortcut on your Desktop.`n2. Select 'Show more options' (if on Windows 11).`n3. Click 'Pin to taskbar'.", "Pin to Taskbar Instructions")

# Open Desktop folder and highlight the shortcut
$shell = New-Object -ComObject Shell.Application
$folder = $shell.Namespace($DesktopPath)
$item = $folder.ParseName("Claire 2.0.lnk")
$item.InvokeVerb("Properties") # Just to show user where it is, or we can use explorer /select
explorer /select,$ShortcutPath
