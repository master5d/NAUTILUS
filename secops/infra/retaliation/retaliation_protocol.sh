#!/bin/bash
# n8n Retaliation Playbook Node Script (To be executed by n8n or directly via SSH on alert)
# Triggered by Falcosidekick -> n8n Webhook

ATTACKER_IP=$1
CONTAINER_NAME=$2
THREAT_LEVEL=$3

echo "[$(date)] 🚨 CRITICAL ALERT INITIATING RETALIATION PROTOCOL"

if [ "$THREAT_LEVEL" == "CRITICAL" ]; then
    echo "[*] Threat Level Critical. Stopping compromised container: $CONTAINER_NAME"
    docker stop $CONTAINER_NAME

    if [ ! -z "$ATTACKER_IP" ]; then
        echo "[*] Adding Attacker IP ($ATTACKER_IP) to CrowdSec Deny List"
        docker exec -t enerv_crowdsec cscli decisions add -i $ATTACKER_IP -d 720h -r "ENERV Retaliation Protocol"
    fi
    
    echo "[!] Container quarantined. Network isolation deployed. Awaiting Architect Review."
    # Trigger Telegram Notification (handled by n8n usually, but fallback here)
fi
