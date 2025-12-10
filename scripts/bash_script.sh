#!/bin/bash

# Configuration
SERVERS_FILE="servers.txt"          # File containing list of servers (one per line)
KEY_FILE="/path/to/private/key"    # Path to your SSH private key
CONF_FILE="/path/to/splunk.conf"   # Full path on remote servers
OLD_PASS="XXX"                      # Password to find
NEW_PASS="YYY"                      # New password
SSH_USER="username"                 # SSH username
LOG_FILE="update_log_$(date +%Y%m%d_%H%M%S).txt"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
SUCCESS=0
FAILED=0

# Function to log messages
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Function to update a single server
update_server() {
    local server=$1
    log "\n${YELLOW}Processing: $server${NC}"
    
    # Create backup
    log "  Creating backup..."
    ssh -i "$KEY_FILE" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "$SSH_USER@$server" "cp $CONF_FILE $CONF_FILE.backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        log "  ${RED}✗ Failed to connect or create backup${NC}"
        ((FAILED++))
        return 1
    fi
    
    # Update the file
    log "  Updating password..."
    ssh -i "$KEY_FILE" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "$SSH_USER@$server" "sed -i 's/password=$OLD_PASS/password=$NEW_PASS/g' $CONF_FILE"
    
    if [ $? -ne 0 ]; then
        log "  ${RED}✗ Failed to update file${NC}"
        ((FAILED++))
        return 1
    fi
    
    # Verify the change
    log "  Verifying change..."
    result=$(ssh -i "$KEY_FILE" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        "$SSH_USER@$server" "grep -c 'password=$NEW_PASS' $CONF_FILE")
    
    if [ "$result" -gt 0 ]; then
        log "  ${GREEN}✓ Successfully updated ($result occurrence(s))${NC}"
        ((SUCCESS++))
        return 0
    else
        log "  ${RED}✗ Verification failed - password not found after update${NC}"
        log "  Restoring backup..."
        ssh -i "$KEY_FILE" -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
            "$SSH_USER@$server" "cp $CONF_FILE.backup_* $CONF_FILE" 2>/dev/null
        ((FAILED++))
        return 1
    fi
}

# Main execution
log "${YELLOW}=== Splunk Config Update Script ===${NC}"
log "Start time: $(date)"
log "Servers file: $SERVERS_FILE"
log "Config file: $CONF_FILE"
log "Replacing: password=$OLD_PASS with password=$NEW_PASS"

# Check if servers file exists
if [ ! -f "$SERVERS_FILE" ]; then
    log "${RED}Error: $SERVERS_FILE not found${NC}"
    exit 1
fi

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    log "${RED}Error: Key file $KEY_FILE not found${NC}"
    exit 1
fi

# Count total servers
TOTAL=$(wc -l < "$SERVERS_FILE")
log "\nTotal servers to process: $TOTAL\n"

# Optional: Ask for confirmation
read -p "Continue with update? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    log "${YELLOW}Update cancelled${NC}"
    exit 0
fi

# Process each server
while IFS= read -r server; do
    # Skip empty lines and comments
    [[ -z "$server" || "$server" =~ ^# ]] && continue
    
    update_server "$server"
done < "$SERVERS_FILE"

# Summary
log "\n${YELLOW}=== Update Summary ===${NC}"
log "Total processed: $TOTAL"
log "${GREEN}Successful: $SUCCESS${NC}"
log "${RED}Failed: $FAILED${NC}"
log "End time: $(date)"
log "Log saved to: $LOG_FILE"
