#!/bin/bash
if [[ "$(uname)" == "Darwin" ]]; then
    hostname -s
else
    cat /proc/sys/kernel/hostname
fi
