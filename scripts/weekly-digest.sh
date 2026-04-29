#!/usr/bin/env bash
# Weekly digest script for Agentic AI project
# Collect health checks and log them
LOG_DIR="/mnt/c/Warp Projects/Agentic AI/logs"
mkdir -p "$LOG_DIR"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
echo "=== Weekly Digest $DATE ===" >> "$LOG_DIR/weekly-digest.log"
echo "LiteLLM health:" >> "$LOG_DIR/weekly-digest.log"
if curl -s http://localhost:4000/health ; then
  curl -s http://localhost:4000/health >> "$LOG_DIR/weekly-digest.log"
else
  echo "LiteLLM health check failed" >> "$LOG_DIR/weekly-digest.log"
fi

echo "LLaMA server health:" >> "$LOG_DIR/weekly-digest.log"
if curl -s http://localhost:8080/health ; then
  curl -s http://localhost:8080/health >> "$LOG_DIR/weekly-digest.log"
else
  echo "LLaMA health check failed" >> "$LOG_DIR/weekly-digest.log"
fi

echo "" >> "$LOG_DIR/weekly-digest.log"
