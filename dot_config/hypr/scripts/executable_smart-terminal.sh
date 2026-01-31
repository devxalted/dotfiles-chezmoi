#!/bin/bash

# Check if any wezterm instances are running
if pgrep -x wezterm-gui > /dev/null || pgrep -x wezterm > /dev/null; then
    # Wezterm already running, spawn in current workspace
    wezterm &
else
    # First terminal, spawn in workspace 1
    hyprctl dispatch workspace 1
    wezterm &
fi
