#!/bin/bash
if [[ "$(uname)" == "Darwin" ]]; then
    total_bytes=$(sysctl -n hw.memsize)
    total_gb=$(echo "scale=1; $total_bytes / 1073741824" | bc)
    page_size=$(sysctl -n hw.pagesize)
    vm_out=$(vm_stat)
    active=$(echo "$vm_out" | awk '/Pages active/ {print $3+0}')
    wired=$(echo "$vm_out" | awk '/Pages wired/ {print $4+0}')
    compressed=$(echo "$vm_out" | awk '/Pages occupied by compressor/ {print $5+0}')
    used_gb=$(echo "scale=1; ($active + $wired + $compressed) * $page_size / 1073741824" | bc)
    printf "%sG/%sG" "$used_gb" "$total_gb"
else
    free -m | awk '/Mem:/ {printf "%.1fG/%.1fG", $3/1024, $2/1024}'
fi
