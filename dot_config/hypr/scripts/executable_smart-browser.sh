#!/bin/bash

TIMESTAMP_FILE="/tmp/hypr-browser-last"
NOW=$(date +%s%3N)  # milliseconds

if [ -f "$TIMESTAMP_FILE" ]; then
    LAST=$(cat "$TIMESTAMP_FILE")
    DIFF=$((NOW - LAST))
    if [ "$DIFF" -lt 400 ]; then
        # Double press: always go to workspace 2
        echo "$NOW" > "$TIMESTAMP_FILE"
        hyprctl dispatch workspace 2
        exit 0
    fi
fi

echo "$NOW" > "$TIMESTAMP_FILE"

# Check if firefox is running anywhere
FIREFOX_RUNNING=$(hyprctl clients -j | jq '[.[] | select(.class == "firefox")] | length')

if [ "$FIREFOX_RUNNING" -eq 0 ]; then
    # Not running at all — launch it on WS 2
    hyprctl dispatch workspace 2
    firefox &
    exit 0
fi

# Check if firefox exists on the current workspace
ACTIVE_WS=$(hyprctl activeworkspace -j | jq -r '.id')
FIREFOX_ON_WS=$(hyprctl clients -j | jq -r --arg ws "$ACTIVE_WS" \
    '[.[] | select(.class == "firefox" and (.workspace.id | tostring) == $ws)] | length')

if [ "$FIREFOX_ON_WS" -gt 0 ]; then
    # Focus existing firefox on current workspace
    hyprctl dispatch focuswindow "class:firefox"
else
    # No firefox here, jump to workspace 2
    hyprctl dispatch workspace 2
fi
