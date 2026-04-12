#!/bin/bash
if [[ "$(uname)" == "Darwin" ]]; then
    top -l 2 -n 0 -s 1 | grep "CPU usage" | tail -1 | awk '{printf "%d%%", $3 + $5}'
else
    read -r cpu1 idle1 < <(awk '/^cpu / {print $2+$3+$4+$6+$7+$8, $5}' /proc/stat)
    sleep 1
    read -r cpu2 idle2 < <(awk '/^cpu / {print $2+$3+$4+$6+$7+$8, $5}' /proc/stat)
    total=$((cpu2 - cpu1 + idle2 - idle1))
    if [ "$total" -gt 0 ]; then
        printf "%d%%" $(( (cpu2 - cpu1) * 100 / total ))
    else
        printf "0%%"
    fi
fi
