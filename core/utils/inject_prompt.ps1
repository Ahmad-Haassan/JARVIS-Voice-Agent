param(
    [string]$WindowTitle = "Antigravity",
    [int]$WaitSec = 6
)

$ws = New-Object -ComObject WScript.Shell

# 1. Loop and wait for the specific target window to appear and bring it to the foreground
$found = $false
for ($i = 0; $i -lt ($WaitSec * 3); $i++) {
    if ($WindowTitle -and $ws.AppActivate($WindowTitle)) {
        $found = $true
        break
    }
    if (-not $WindowTitle -and $ws.AppActivate("Antigravity")) {
        $found = $true
        break
    }
    Start-Sleep -Milliseconds 350
}

if (-not $found) {
    exit 1
}

# 2. Allow focus to settle
Start-Sleep -Milliseconds 800

# 3. Open/Focus AI Agent Chat (Ctrl + L)
$ws.SendKeys("^l")
Start-Sleep -Milliseconds 600

# 4. Paste Prompt from Clipboard (Ctrl + V)
$ws.SendKeys("^v")
Start-Sleep -Milliseconds 400

# 5. Submit Prompt to AI (Enter)
$ws.SendKeys("~")
