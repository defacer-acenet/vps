#!/bin/bash
clear
while true; do
  sudo apt update
  clear
  echo "🟢 Still alive at $(date)"
  sleep 60
done
