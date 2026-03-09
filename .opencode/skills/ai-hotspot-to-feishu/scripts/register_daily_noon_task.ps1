param(
    [string]$TaskName = "AIHotspotToFeishuNoon",
    [int]$Limit = 10,
    [int]$Hours = 24,
    [string]$SummaryDepth = "detailed"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "sync_ai_hotspot_to_feishu.py"
$pythonPath = "C:\Progra~1\Python313\python.exe"
$taskCommand = "$pythonPath $scriptPath --limit $Limit --hours $Hours --summary-depth $SummaryDepth"

schtasks /Create /SC DAILY /TN $TaskName /TR $taskCommand /ST 12:00 /F | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Output "已创建计划任务: $TaskName，每天 12:00 执行。"
} else {
    Write-Error "创建计划任务失败，请检查权限后重试。"
    exit 1
}
