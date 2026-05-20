#!/usr/bin/env bash
# Weekly digest script for SOVRN / Agentic AI stack
# Collect health checks and log them to Calendar/Logs

LOG_DIR="/mnt/c/telo/Calendar/Logs"
mkdir -p "$LOG_DIR"
DATE=$(date "+%Y-%m-%d %H:%M:%S")

echo "=== Weekly Digest $DATE ===" >> "$LOG_DIR/weekly-digest.log"
echo "Weekly Digest for Agentic AI - $DATE"
echo "-----------------------------------"
echo "Project Status: Active"

echo "LiteLLM health:" >> "$LOG_DIR/weekly-digest.log"
if curl -s http://localhost:4000/health ; then
  curl -s http://localhost:4000/health >> "$LOG_DIR/weekly-digest.log"
  echo "✔ LiteLLM OK"
else
  echo "LiteLLM health check failed" >> "$LOG_DIR/weekly-digest.log"
  echo "✖ LiteLLM FAILED"
fi

echo "LLaMA server health:" >> "$LOG_DIR/weekly-digest.log"
if curl -s http://localhost:8080/health ; then
  curl -s http://localhost:8080/health >> "$LOG_DIR/weekly-digest.log"
  echo "✔ LLaMA Server OK"
else
  echo "LLaMA health check failed" >> "$LOG_DIR/weekly-digest.log"
  echo "✖ LLaMA Server FAILED"
fi

echo "" >> "$LOG_DIR/weekly-digest.log"