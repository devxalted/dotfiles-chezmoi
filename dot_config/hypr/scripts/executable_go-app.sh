#!/bin/bash
# go-app.sh <window-class> <workspace> <launch-command>
# Jumps to the app's workspace if running, otherwise launches it there.

CLASS="$1"
WS="$2"
CMD="$3"

if [ -z "$CLASS" ] || [ -z "$WS" ] || [ -z "$CMD" ]; then
    echo "Usage: go-app.sh <window-class> <workspace> <launch-command>"
    exit 1
fi

RUNNING=$(hyprctl clients -j | jq -r --arg class "$CLASS" \
    '[.[] | select(.class == $class)] | length')

if [ "$RUNNING" -gt 0 ]; then
    hyprctl dispatch movetoworkspace "$WS,class:^($CLASS)$"
    hyprctl dispatch workspace "$WS"
else
    hyprctl dispatch workspace "$WS"
    eval "$CMD" &
fi
