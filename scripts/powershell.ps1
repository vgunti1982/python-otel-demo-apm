# Configuration
$ServersFile = "servers.txt"
$KeyFile = "C:\path\to\private\key"
$ConfFile = "/path/to/splunk.conf"
$OldPass = "XXX"
$NewPass = "YYY"
$SshUser = "username"
$LogFile = "update_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"

# Counters
$Success = 0
$Failed = 0

# Function to log messages
function Log-Message {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] $Message"
    
    switch($Color) {
        "Green" { Write-Host $LogEntry -ForegroundColor Green }
        "Red" { Write-Host $LogEntry -ForegroundColor Red }
        "Yellow" { Write-Host $LogEntry -ForegroundColor Yellow }
        default { Write-Host $LogEntry }
    }
    
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to execute SSH command
function Invoke-SshCommand {
    param(
        [string]$Server,
        [string]$Command
    )
    
    try {
        $SshCommand = @(
            "-i", $KeyFile,
            "-o", "ConnectTimeout=5",
            "-o", "StrictHostKeyChecking=no",
            "$($SshUser)@$Server",
            $Command
        )
        
        $output = & ssh $SshCommand 2>&1
        $exitCode = $LASTEXITCODE
        
        return @{
            Success = ($exitCode -eq 0)
            Output = $output -join "`n"
            ExitCode = $exitCode
        }
    }
    catch {
        return @{
            Success = $false
            Output = ""
            ExitCode = -1
            Error = $_.Exception.Message
        }
    }
}

# Function to update a single server
function Update-Server {
    param(
        [string]$Server
    )
    
    Log-Message "Processing: $Server" "Yellow"
    
    # Create backup
    Log-Message "  Creating backup..." "Yellow"
    $BackupCmd = "cp $ConfFile $ConfFile.backup_$(date +%Y%m%d_%H%M%S)"
    $BackupResult = Invoke-SshCommand -Server $Server -Command $BackupCmd
    
    if (-not $BackupResult.Success) {
        Log-Message "  ✗ Failed to connect or create backup: $($BackupResult.Output)" "Red"
        return $false
    }
    
    # Update the file
    Log-Message "  Updating password..." "Yellow"
    $UpdateCmd = "sed -i 's/password=$OldPass/password=$NewPass/g' $ConfFile"
    $UpdateResult = Invoke-SshCommand -Server $Server -Command $UpdateCmd
    
    if (-not $UpdateResult.Success) {
        Log-Message "  ✗ Failed to update file: $($UpdateResult.Output)" "Red"
        return $false
    }
    
    # Verify the change
    Log-Message "  Verifying change..." "Yellow"
    $VerifyCmd = "grep -c 'password=$NewPass' $ConfFile"
    $VerifyResult = Invoke-SshCommand -Server $Server -Command $VerifyCmd
    
    if ($VerifyResult.Success -and $VerifyResult.Output -match '^\d+$') {
        $Count = [int]$VerifyResult.Output
        if ($Count -gt 0) {
            Log-Message "  ✓ Successfully updated ($Count occurrence(s))" "Green"
            return $true
        }
    }
    
    # Verification failed - restore backup
    Log-Message "  ✗ Verification failed - restoring backup" "Red"
    $RestoreCmd = "cp $ConfFile.backup_* $ConfFile 2>/dev/null"
    Invoke-SshCommand -Server $Server -Command $RestoreCmd | Out-Null
    
    return $false
}

# Main execution
function Main {
    Log-Message "=== Splunk Config Update Script ===" "Yellow"
    Log-Message "Start time: $(Get-Date)"
    Log-Message "Config file: $ConfFile"
    Log-Message "Replacing: password=$OldPass with password=$NewPass"
    Log-Message ""
    
    # Verify files exist
    if (-not (Test-Path $ServersFile)) {
        Log-Message "Error: $ServersFile not found" "Red"
        exit 1
    }
    
    if (-not (Test-Path $KeyFile)) {
        Log-Message "Error: Key file $KeyFile not found" "Red"
        exit 1
    }
    
    # Check SSH is available
    try {
        $sshVersion = ssh -V 2>&1
        Log-Message "SSH available: $sshVersion" "Green"
    }
    catch {
        Log-Message "Error: SSH not found or not in PATH" "Red"
        exit 1
    }
    
    # Read servers
    $Servers = @(Get-Content $ServersFile | Where-Object { $_ -and -not $_.StartsWith("#") })
    $Total = $Servers.Count
    
    Log-Message "Total servers to process: $Total"
    Log-Message ""
    
    # Confirmation
    $Confirm = Read-Host "Continue with update? (yes/no)"
    if ($Confirm -ne "yes") {
        Log-Message "Update cancelled" "Yellow"
        exit 0
    }
    
    Log-Message ""
    
    # Process each server
    foreach ($Server in $Servers) {
        $Server = $Server.Trim()
        if ($Server) {
            if (Update-Server -Server $Server) {
                $Script:Success++
            }
            else {
                $Script:Failed++
            }
        }
    }
    
    # Summary
    Log-Message ""
    Log-Message "=== Update Summary ===" "Yellow"
    Log-Message "Total processed: $Total"
    Log-Message "Successful: $Success" "Green"
    Log-Message "Failed: $Failed" "Red"
    Log-Message "End time: $(Get-Date)"
    Log-Message "Log saved to: $LogFile"
}

# Run main function
Main
