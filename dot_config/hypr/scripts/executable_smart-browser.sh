#!/bin/bash

# Get current workspace
CURRENT_WS=$(hyprctl activeworkspace -j | grep -o '"id":[0-9]*' | cut -d':' -f2)

# Check if firefox is running
if pgrep -f firefox > /dev/null; then
    # Firefox is running
    if [ "$CURRENT_WS" = "2" ]; then
        # Already on workspace 2, spawn another browser
        firefox &
    else
        # Not on workspace 2, just switch to it
        hyprctl dispatch workspace 2
    fi
else
    # First browser, spawn in workspace 2
    hyprctl dispatch workspace 2
    firefox &
fi
