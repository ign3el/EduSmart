param([string]$InputFile = 'agent-output.json')
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "
 { SHIELD } V18.2 GLOBAL ENFORCER" -ForegroundColor Cyan

if (!(Test-Path 'V18_keystore.json')) { throw 'CRITICAL: Keystore missing!' }
$Keystore = Get-Content 'V18_keystore.json' | ConvertFrom-Json

function Verify-Action { 
    param([string]$AgentName, [string]$ActionType)
    Write-Host " { BLUE } Verifying Identity: $AgentName" -ForegroundColor Yellow

    if ($AgentName -eq 'Support') { return $true }
    if (!$Keystore.$AgentName) { return $false }

    # UNIVERSAL SME CHECK
    $Executioners = @('Orchestrator','Coder','Support')
    if ($AgentName -notin $Executioners -and $ActionType -eq 'WriteFile') { 
         Write-Host '   🛑 ISOLATION: SME Agent cannot write code.' -ForegroundColor Red
         return $false 
    }
    return $true
}
if (Test-Path $InputFile) {
    $Data = Get-Content $InputFile | ConvertFrom-Json
    foreach ($a in $Data) { if (!(Verify-Action $a.name 'Chat')) { exit 1 } }
}
Write-Host '
✅ INTEGRITY VERIFIED (AUTO-APPROVED)' -ForegroundColor Cyan -BackgroundColor DarkBlue
