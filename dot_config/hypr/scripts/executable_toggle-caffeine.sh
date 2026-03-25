#!/usr/bin/env bash
# Toggle sleep inhibitor (caffeine mode)

PIDFILE="/tmp/caffeine-inhibit.pid"

if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    # Currently active — disable
    kill "$(cat "$PIDFILE")"
    rm -f "$PIDFILE"
    dunstify -a "Caffeine" -u normal -i coffee -r 9999 "Caffeine OFF" "Sleep is allowed"
else
    # Enable — hold an inhibit lock in the background
    systemd-inhibit --what=sleep:idle --who="Caffeine" --why="User toggled caffeine mode" sleep infinity &
    echo $! > "$PIDFILE"
    dunstify -a "Caffeine" -u normal -i coffee -r 9999 "Caffeine ON" "Sleep is inhibited"
fi
