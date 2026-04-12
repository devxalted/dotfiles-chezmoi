#!/bin/bash
if [[ "$(uname)" == "Darwin" ]]; then
    sysctl -n vm.loadavg | awk '{printf "%.2f", $2}'
else
    awk '{printf "%.2f", $1}' /proc/loadavg
fi
