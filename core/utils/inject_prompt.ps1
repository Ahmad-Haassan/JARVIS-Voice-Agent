param(
    [string]$WindowTitle = "Antigravity",
    [int]$WaitSec = 3
)

$ws = New-Object -ComObject WScript.Shell

# 1. Bring window to front
if ($WindowTitle) {
    $ws.AppActivate($WindowTitle)
} else {
    $ws.AppActivate("Antigravity")
}

# 2. Allow focus to settle
Start-Sleep -Seconds $WaitSec

# 3. Direct Ctrl + V and Enter
$ws.SendKeys("^v")
Start-Sleep -Milliseconds 300
$ws.SendKeys("~")
