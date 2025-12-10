#!/usr/bin/env python3

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configuration
SERVERS_FILE = "servers.txt"
KEY_FILE = "/path/to/private/key"
CONF_FILE = "/path/to/splunk.conf"
OLD_PASS = "XXX"
NEW_PASS = "YYY"
SSH_USER = "username"

# Counters
success = 0
failed = 0

def log_message(msg, color=None):
    """Print and log messages"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    colors = {
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        'end': '\033[0m'
    }
    
    if color and color in colors:
        print(f"{colors[color]}[{timestamp}] {msg}{colors['end']}")
    else:
        print(f"[{timestamp}] {msg}")
    
    with open(f"update_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def run_ssh_command(server, command):
    """Execute SSH command on remote server"""
    try:
        result = subprocess.run(
            [
                "ssh", 
                "-i", KEY_FILE,
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=no",
                f"{SSH_USER}@{server}",
                command
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Connection timeout"
    except Exception as e:
        return False, "", str(e)

def update_server(server):
    """Update Splunk config on a single server"""
    global success, failed
    
    log_message(f"Processing: {server}", 'yellow')
    
    # Create backup
    log_message(f"  Creating backup...", 'yellow')
    backup_cmd = f"cp {CONF_FILE} {CONF_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
    success_backup, _, err = run_ssh_command(server, backup_cmd)
    
    if not success_backup:
        log_message(f"  ✗ Failed to connect or create backup: {err}", 'red')
        failed += 1
        return False
    
    # Update the file
    log_message(f"  Updating password...", 'yellow')
    update_cmd = f"sed -i 's/password={OLD_PASS}/password={NEW_PASS}/g' {CONF_FILE}"
    success_update, _, err = run_ssh_command(server, update_cmd)
    
    if not success_update:
        log_message(f"  ✗ Failed to update file: {err}", 'red')
        failed += 1
        return False
    
    # Verify the change
    log_message(f"  Verifying change...", 'yellow')
    verify_cmd = f"grep -c 'password={NEW_PASS}' {CONF_FILE}"
    success_verify, output, _ = run_ssh_command(server, verify_cmd)
    
    if success_verify and output.strip().isdigit() and int(output.strip()) > 0:
        log_message(f"  ✓ Successfully updated ({output.strip()} occurrence(s))", 'green')
        success += 1
        return True
    else:
        log_message(f"  ✗ Verification failed - restoring backup", 'red')
        restore_cmd = f"cp {CONF_FILE}.backup_* {CONF_FILE} 2>/dev/null"
        run_ssh_command(server, restore_cmd)
        failed += 1
        return False

def main():
    """Main execution"""
    global success, failed
    
    log_message("=== Splunk Config Update Script ===", 'yellow')
    log_message(f"Start time: {datetime.now()}")
    log_message(f"Config file: {CONF_FILE}")
    log_message(f"Replacing: password={OLD_PASS} with password={NEW_PASS}")
    
    # Verify files exist
    if not Path(SERVERS_FILE).exists():
        log_message(f"Error: {SERVERS_FILE} not found", 'red')
        sys.exit(1)
    
    if not Path(KEY_FILE).exists():
        log_message(f"Error: Key file {KEY_FILE} not found", 'red')
        sys.exit(1)
    
    # Read servers
    with open(SERVERS_FILE, 'r') as f:
        servers = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    total = len(servers)
    log_message(f"\nTotal servers to process: {total}\n")
    
    # Confirmation
    confirm = input("Continue with update? (yes/no): ").lower()
    if confirm != "yes":
        log_message("Update cancelled", 'yellow')
        sys.exit(0)
    
    # Process servers
    for server in servers:
        update_server(server)
    
    # Summary
    log_message(f"\n=== Update Summary ===", 'yellow')
    log_message(f"Total processed: {total}")
    log_message(f"Successful: {success}", 'green')
    log_message(f"Failed: {failed}", 'red')
    log_message(f"End time: {datetime.now()}")

if __name__ == "__main__":
    main()
