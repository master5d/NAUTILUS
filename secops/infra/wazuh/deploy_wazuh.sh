#!/bin/bash
# ENERV Wazuh SIEM Deployment Script
# Orchestrates the secure installation of Wazuh on the Hetzner Node

cd /mnt/c/telo/secops/wazuh
echo "[*] Generating Certificates..."
bash wazuh-install.sh --generate-config-files

echo "[*] Installing Wazuh Indexer..."
bash wazuh-install.sh --wazuh-indexer node-1

echo "[*] Initializing Wazuh Indexer Cluster..."
bash wazuh-install.sh --start-cluster

echo "[*] Installing Wazuh Server..."
bash wazuh-install.sh --wazuh-server wazuh-1

echo "[*] Installing Wazuh Dashboard..."
bash wazuh-install.sh --wazuh-dashboard dashboard

echo "[*] Wazuh Installation Complete."
echo "[!] IMPORTANT: Extract passwords by running: tar -O -xvf wazuh-install-files.tar wazuh-install-files/wazuh-passwords.txt"
