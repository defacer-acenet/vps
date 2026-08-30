#!/usr/bin/env bash

# ==========================================
# Network Speed Test - Fast.com style
# ==========================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${CYAN}========================================${RESET}"
echo -e "${CYAN}        INTERNET SPEED TEST${RESET}"
echo -e "${CYAN}========================================${RESET}"
echo

# Kiểm tra speedtest
if ! command -v speedtest >/dev/null 2>&1; then
    echo -e "${YELLOW}Chưa cài Ookla Speedtest CLI,để tôi cài.${RESET}"
    if [[ "$(uname)" == "Linux" ]]; then
        sudo apt install speedtest-cli
    else
        brew install speedtest-cli
    fi
fi

echo -e "${YELLOW}Đang kiểm tra tốc độ...${RESET}"
echo

# Chạy speedtest
RESULT=$(speedtest --simple)

PING=$(echo "$RESULT" | awk '/Ping/ {print $2}')
DOWNLOAD=$(echo "$RESULT" | awk '/Download/ {print $2}')
UPLOAD=$(echo "$RESULT" | awk '/Upload/ {print $2}')

# Kiểm tra kết quả
if [[ -z "$DOWNLOAD" || -z "$UPLOAD" ]]; then
    echo -e "${RED}Không thể lấy kết quả speedtest.${RESET}"
    exit 1
fi

# Tính tốc độ tổng kết:
# lấy trung bình download + upload
TOTAL=$(awk -v d="$DOWNLOAD" -v u="$UPLOAD" \
    'BEGIN { printf "%.2f", (d + u) / 2 }')

echo -e "${GREEN}Ping:${RESET}       ${PING} ms"
echo -e "${GREEN}Download:${RESET}   ${DOWNLOAD} Mbit/s"
echo -e "${GREEN}Upload:${RESET}     ${UPLOAD} Mbit/s"
echo
echo -e "${CYAN}----------------------------------------${RESET}"
echo -e "${GREEN}TỔNG KẾT:${RESET}   ${TOTAL} Mbit/s"
echo -e "${CYAN}----------------------------------------${RESET}"
