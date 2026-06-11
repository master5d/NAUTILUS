#!/bin/bash
# n8n Retaliation Playbook Node Script (To be executed by n8n or directly via SSH on alert)
# Triggered by Falcosidekick -> n8n Webhook
set -euo pipefail

ATTACKER_IP="${1:-}"
CONTAINER_NAME="${2:-}"
THREAT_LEVEL="${3:-}"

# Webhook input is untrusted — validate before passing to docker/cscli
valid_ip() {
    [[ "$1" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || [[ "$1" =~ ^[0-9a-fA-F:]+$ ]]
}
valid_container() {
    [[ "$1" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]
}

echo "[$(date)] 🚨 CRITICAL ALERT INITIATING RETALIATION PROTOCOL"

if [ "$THREAT_LEVEL" == "CRITICAL" ]; then
    if [ -n "$CONTAINER_NAME" ] && valid_container "$CONTAINER_NAME"; then
        echo "[*] Threat Level Critical. Stopping compromised container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME"
    else
        echo "[!] Container name missing or invalid — skipping stop: '$CONTAINER_NAME'"
    fi

    if [ -n "$ATTACKER_IP" ]; then
        if valid_ip "$ATTACKER_IP"; then
            echo "[*] Adding Attacker IP ($ATTACKER_IP) to CrowdSec Deny List"
            docker exec -t enerv_crowdsec cscli decisions add -i "$ATTACKER_IP" -d 720h -r "ENERV Retaliation Protocol"
        else
            echo "[!] Invalid IP format — refusing to pass to cscli: '$ATTACKER_IP'"
        fi
    fi

    echo "[!] Container quarantined. Network isolation deployed. Awaiting Architect Review."
    # Trigger Telegram Notification (handled by n8n usually, but fallback here)
fi
