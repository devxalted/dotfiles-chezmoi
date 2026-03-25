#!/bin/bash
awk '{printf "%.2f", $1}' /proc/loadavg
