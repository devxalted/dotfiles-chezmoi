#!/bin/bash

# Kill the zenity window if it exists
if [ -f /tmp/hypr-keybinds.pid ]; then
    kill $(cat /tmp/hypr-keybinds.pid) 2>/dev/null
    rm /tmp/hypr-keybinds.pid
fi
