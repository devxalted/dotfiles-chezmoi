#!/bin/bash

hyprctl dispatch workspace 1
ADDR=$(hyprctl clients -j | jq -r '[.[] | select(.class == "org.wezfurlong.wezterm" and .workspace.id == 1)] | first | .address')
if [ -n "$ADDR" ] && [ "$ADDR" != "null" ]; then
    hyprctl dispatch focuswindow "address:$ADDR"
fi
