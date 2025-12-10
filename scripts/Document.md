# Splunk Configuration Update Scripts - Complete Documentation

## Overview

This documentation covers three scripts for updating the Splunk configuration file (`splunk.conf`) across 100+ Linux servers from a VDI jump host. All three scripts provide identical functionality with the same safety features:

- Automatic backup before updates
- Verification of changes
- Automatic rollback on failure
- Detailed logging with timestamps
- Progress tracking and summary reports

---

## Table of Contents

1. [General Setup](#general-setup)
2. [Bash Script](#bash-script)
3. [Python Script](#python-script)
4. [PowerShell Script](#powershell-script)
5. [Comparison & Recommendations](#comparison--recommendations)
6. [Troubleshooting](#troubleshooting)

---

## General Setup

### Prerequisites for All Scripts

1. **SSH Access**: Passwordless SSH configured with private key
2. **Server List**: Create a `servers.txt` file containing server hostnames/IPs (one per line)
3. **Access to VDI/Jump Host**: Where you'll run the script
4. **Required Tools**: 
   - `ssh` (OpenSSH client)
   - `sed` (available on all Linux systems)
   - `grep` (available on all Linux systems)

### Creating the Server List

Create a file named `servers.txt` in the same directory as your script:

```
server1.example.com
server2.example.com
server3.example.com
server4.example.com
# Comments are supported (lines starting with #)
server5.example.com
```

### SSH Key Configuration

Before running any script, ensure passwordless SSH is configured:

```bash
# Test SSH connection
ssh -i /path/to/private/key -o StrictHostKeyChecking=no username@server1.example.com "echo Connected"
```

If this works without prompting for a password, you're good to proceed.

---

## Bash Script

### Requirements

- Bash shell (available on all Linux/macOS)
- SSH client
- `sed`, `grep`, `cp` (standard Linux utilities)
- No additional dependencies

### Setup

1. Copy the Bash script to your VDI
2. Update configuration variables at the top of the script:

```bash
SERVERS_FILE="servers.txt"              # Path to server list
KEY_FILE="/path/to/private/key"        # SSH private key location
CONF_FILE="/path/to/splunk.conf"       # Full path on remote servers
OLD_PASS="XXX"                          # Current password in config
NEW_PASS="YYY"                          # New password to set
SSH_USER="username"                     # SSH username
```

### Usage

```bash
# Make script executable
chmod +x update_splunk.sh

# Run the script
./update_splunk.sh
```

### Output Example

```
Processing: server1.example.com
  Creating backup...
  Updating password...
  Verifying change...
  ✓ Successfully updated (1 occurrence(s))

Processing: server2.example.com
  Creating backup...
  Updating password...
  Verifying change...
  ✓ Successfully updated (2 occurrence(s))

=== Update Summary ===
Total processed: 100
Successful: 98
Failed: 2
Log saved to: update_log_20231215_143022.txt
```

### Advantages

- Lightweight and fast
- No dependencies beyond standard Linux tools
- Works on any Linux/macOS system
- Lowest resource overhead for 100+ servers
- Can run in parallel easily if needed

### Performance Tips

For very large deployments (200+ servers), use GNU Parallel to parallelize updates:

```bash
# Install GNU Parallel (on Linux)
sudo apt-get install parallel

# Run updates with 10 concurrent connections
cat servers.txt | parallel -j 10 "./update_single_server.sh {}"
```

---

## Python Script

### Requirements

- Python 3.6 or higher
- SSH client
- `subprocess` module (built-in)

### Setup

1. Copy the Python script to your VDI
2. Ensure Python 3 is available:

```bash
python3 --version
```

3. Update configuration variables in the script:

```python
SERVERS_FILE = "servers.txt"
KEY_FILE = "/path/to/private/key"
CONF_FILE = "/path/to/splunk.conf"
OLD_PASS = "XXX"
NEW_PASS = "YYY"
SSH_USER = "username"
```

### Usage

```bash
# Make script executable
chmod +x update_splunk.py

# Run with Python 3
python3 update_splunk.py

# Or if executable bit is set
./update_splunk.py
```

### Output Example

```
[2023-12-15 14:30:22] === Splunk Config Update Script ===
[2023-12-15 14:30:22] Start time: 2023-12-15 14:30:22.123456
[2023-12-15 14:30:22] Config file: /path/to/splunk.conf
[2023-12-15 14:30:22] Total servers to process: 100

Processing: server1.example.com
  [2023-12-15 14:30:22] Creating backup...
  [2023-12-15 14:30:23] Updating password...
  [2023-12-15 14:30:23] Verifying change...
  [2023-12-15 14:30:23] ✓ Successfully updated (1 occurrence(s))

=== Update Summary ===
Total processed: 100
Successful: 98
Failed: 2
```

### Advantages

- More readable and maintainable code
- Better error handling and exception management
- Easier to extend with additional features
- Good for teams with Python expertise
- Cross-platform (Windows, Linux, macOS)

### Extending Python Script

To add custom logic, modify the `update_server()` function:

```python
def update_server(server):
    # Add custom pre-update checks
    # Add custom post-update actions
    # Add custom verification logic
    pass
```

---

## PowerShell Script

### Requirements

- Windows PowerShell 5.1+ or PowerShell Core 7+
- OpenSSH client installed on Windows
- Network access to Linux servers from VDI

### Setup

#### 1. Install OpenSSH Client (if not present)

Open PowerShell as Administrator and run:

```powershell
# Check if SSH is installed
ssh -V

# If not installed, install it
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

#### 2. Set Execution Policy (if needed)

```powershell
# Check current policy
Get-ExecutionPolicy

# Set to allow script execution (if restricted)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 3. Update Script Configuration

Edit the PowerShell script and update these variables:

```powershell
$ServersFile = "servers.txt"
$KeyFile = "C:\path\to\private\key"
$ConfFile = "/path/to/splunk.conf"
$OldPass = "XXX"
$NewPass = "YYY"
$SshUser = "username"
```

### Usage

```powershell
# Navigate to script directory
cd C:\path\to\scripts

# Run the script
.\Update-Splunk.ps1

# Or run with explicit PowerShell
powershell -ExecutionPolicy Bypass -File Update-Splunk.ps1
```

### Output Example

The PowerShell version includes colored console output:
- Green text for successful operations
- Red text for errors
- Yellow text for status updates

### Advantages

- Native Windows environment integration
- Colored console output for better visibility
- Better error handling with try-catch blocks
- Easier integration with Windows monitoring tools
- Object-oriented approach for extensibility

### Windows-Specific Considerations

1. **Path separators**: Use backslashes for Windows paths, forward slashes for remote Linux paths
2. **SSH key permissions**: Ensure proper permissions on private key file
3. **Firewall**: Ensure VDI firewall allows outbound SSH (port 22)

### Extending PowerShell Script

To add pre-update or post-update actions:

```powershell
function Pre-Update-Check {
    param([string]$Server)
    # Add pre-update validation
}

function Post-Update-Action {
    param([string]$Server)
    # Add post-update actions (e.g., service restart)
}
```

---

## Comparison & Recommendations

### Feature Comparison

| Feature | Bash | Python | PowerShell |
|---------|------|--------|------------|
| **Execution Speed** | Fastest | Fast | Fast |
| **Dependencies** | Minimal | Python 3 | PowerShell + SSH |
| **Error Handling** | Basic | Excellent | Excellent |
| **Cross-Platform** | Linux/macOS | All platforms | Windows primary |
| **Learning Curve** | Medium | Easy | Medium |
| **Maintainability** | Medium | High | High |
| **Windows Native** | No | No | Yes |
| **Parallelization** | Easy with GNU Parallel | Moderate | Moderate |

### Which Script to Choose?

**Choose Bash if:**
- Running from Linux/macOS VDI
- You want the fastest execution
- You prefer minimal dependencies
- You're comfortable with shell scripting
- You need to parallelize for 200+ servers

**Choose Python if:**
- You want the most maintainable code
- Your team has Python expertise
- You need to add custom logic frequently
- You want cross-platform compatibility
- You prefer object-oriented programming

**Choose PowerShell if:**
- Running from Windows VDI
- You need Windows ecosystem integration
- You prefer graphical error reporting
- Your organization standardizes on PowerShell
- You want native Windows path support

---

## Troubleshooting

### Common Issues and Solutions

#### SSH Connection Failures

**Problem**: "Permission denied (publickey)"

```bash
# Solution: Verify SSH key permissions
chmod 600 /path/to/private/key
chmod 700 ~/.ssh

# Test connection manually
ssh -i /path/to/private/key -vvv username@server1.example.com
```

#### "Command not found: sed" or "Command not found: grep"

**Problem**: Required tools not available on remote system

**Solution**: Install on remote servers:
```bash
# For RHEL/CentOS
sudo yum install sed grep

# For Ubuntu/Debian
sudo apt-get install sed grep
```

#### Script Hangs or Times Out

**Problem**: Connection to one server hangs entire script

**Solution**: Increase timeout or use connection pooling:

```bash
# Bash: Add timeout
timeout 30 ssh -i $KEY_FILE -o ConnectTimeout=5 $SSH_USER@$server "command"

# Python: Timeout already set to 30 seconds in subprocess calls
```

#### Permission Denied Updating File

**Problem**: User doesn't have write permission to `splunk.conf`

**Solution**: Run with sudo or escalate privileges:

```bash
# Update sed command to use sudo
ssh -i "$KEY_FILE" "$SSH_USER@$server" "sudo sed -i 's/password=$OLD_PASS/password=$NEW_PASS/g' $CONF_FILE"

# May need to configure passwordless sudo
```

#### "Servers.txt not found"

**Problem**: Script can't find server list

**Solution**: Ensure file is in the same directory as script:
```bash
# Bash/Python
ls -la servers.txt

# PowerShell
Get-Item servers.txt
```

#### Backup Restore Issues

**Problem**: Automatic rollback doesn't work

**Solution**: Manually restore from backup:
```bash
# On remote server
ssh username@server1 "cp /path/to/splunk.conf.backup_* /path/to/splunk.conf"

# Verify
ssh username@server1 "grep password /path/to/splunk.conf"
```

### Verification Commands

To manually verify updates on a server:

```bash
# Check if new password exists
ssh -i /path/to/key username@server "grep password=/path/to/splunk.conf"

# Count occurrences
ssh -i /path/to/key username@server "grep -c 'password=YYY' /path/to/splunk.conf"

# View backups
ssh -i /path/to/key username@server "ls -la /path/to/splunk.conf*"
```

---

## Best Practices

1. **Always test first**: Run the script on 2-3 servers before full rollout
2. **Backup everything**: The scripts create backups, but maintain your own backup copy
3. **Schedule updates**: Plan updates during maintenance windows
4. **Monitor the log**: Check the generated log file for any issues
5. **Verify connectivity**: Test SSH to 10+ random servers before running
6. **Run from stable location**: Execute from jump host with consistent network access
7. **Document the change**: Keep a record of what was changed and when
8. **Plan rollback**: Know how to quickly restore from backups if needed

---

## Support and Logging

All scripts generate timestamped log files:

- **Bash**: `update_log_YYYYMMDD_HHMMSS.txt`
- **Python**: `update_log_YYYYMMDD_HHMMSS.txt`
- **PowerShell**: `update_log_YYYYMMDD_HHMMSS.txt`

These logs contain:
- Timestamp of each operation
- Server name being processed
- Success/failure status
- Error messages (if any)
- Final summary with counts

Keep logs for audit and troubleshooting purposes.

---

## Next Steps

1. Choose the appropriate script for your environment
2. Create `servers.txt` with your server list
3. Test SSH connectivity to a few servers
4. Update configuration variables in the script
5. Run the script on a small subset first (5-10 servers)
6. Review the log file for any issues
7. If successful, run on full server list
8. Verify updates on random sample of servers
9. Keep log file and backups for 30 days
