#!/bin/bash

clear

echo "===== DUNG LƯỢNG Ổ ĐĨA ====="
echo

df -h --output=source,size,used,avail,pcent,target | head -n 1
df -h --output=source,size,used,avail,pcent,target | tail -n +2

echo
echo "===== CẢNH BÁO ====="

df -P | tail -n +2 | while read -r filesystem blocks used available capacity mountpoint
do
    usage=${capacity%\%}

    if [ "$usage" -ge 90 ]; then
        echo "⚠️  Cảnh báo: $mountpoint đã sử dụng ${usage}%"
    elif [ "$usage" -ge 80 ]; then
        echo "⚠️  $mountpoint đã sử dụng ${usage}%"
    fi
done
