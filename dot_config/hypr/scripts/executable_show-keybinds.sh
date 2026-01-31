#!/bin/bash

# Toggle: if already running, kill it; otherwise, show it
if [ -f /tmp/hypr-keybinds.pid ]; then
    PID=$(cat /tmp/hypr-keybinds.pid)
    if kill -0 "$PID" 2>/dev/null; then
        # Process is running, kill it
        kill "$PID" 2>/dev/null
        rm /tmp/hypr-keybinds.pid
        exit 0
    else
        # PID file exists but process is dead, clean up
        rm /tmp/hypr-keybinds.pid
    fi
fi

CONFIG="$HOME/.config/hypr/hyprland.conf"

# Parse keybindings and organize by category
generate_keybinds() {
    cat << 'HEADER'
╔═══════════════════════════════════════════════════════════════╗
║             HYPRLAND KEYBINDINGS CHEAT SHEET                  ║
╚═══════════════════════════════════════════════════════════════╝

HEADER

    echo "🚀 APPLICATION LAUNCHERS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bind.*exec.*\(smart-terminal\|smart-browser\|fileManager\|discord\|spotify\|menu\)" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, exec,/ →/' | \
        sed 's/~\/.config\/hypr\/scripts\/smart-terminal.sh/Terminal (wezterm)/' | \
        sed 's/~\/.config\/hypr\/scripts\/smart-browser.sh/Browser (Zen)/' | \
        sed 's/$fileManager/File Manager/' | \
        sed 's/$discord/Discord/' | \
        sed 's/spotify/Spotify/' | \
        sed 's/$menu/App Launcher/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "🪟 WINDOW MANAGEMENT"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bind.*\(killactive\|fullscreen\|togglefloating\|pseudo\|togglesplit\|togglegroup\|changegroupactive\)" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, killactive,/ → Close window/' | \
        sed 's/, fullscreen, 0/ → Fullscreen/' | \
        sed 's/, fullscreen, 1/ → Maximize/' | \
        sed 's/, togglefloating,/ → Toggle floating/' | \
        sed 's/, pseudo,/ → Pseudo-tile/' | \
        sed 's/, togglesplit,/ → Toggle split/' | \
        sed 's/, togglegroup,/ → Toggle group/' | \
        sed 's/, changegroupactive, f/ → Next window in group/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "🧭 FOCUS NAVIGATION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bind.*movefocus" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, movefocus, l/ → Focus left/' | \
        sed 's/, movefocus, r/ → Focus right/' | \
        sed 's/, movefocus, u/ → Focus up/' | \
        sed 's/, movefocus, d/ → Focus down/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "📦 MOVE WINDOWS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bind.*movewindow" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, movewindow, l/ → Move left/' | \
        sed 's/, movewindow, r/ → Move right/' | \
        sed 's/, movewindow, u/ → Move up/' | \
        sed 's/, movewindow, d/ → Move down/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "↔️  RESIZE WINDOWS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^binde.*resizeactive" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/binde\s*=\s*//' | \
        sed 's/, resizeactive, -30 0/ → Resize left/' | \
        sed 's/, resizeactive, 30 0/ → Resize right/' | \
        sed 's/, resizeactive, 0 -30/ → Resize up/' | \
        sed 's/, resizeactive, 0 30/ → Resize down/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "🗂️  WORKSPACES"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Super + [1-9,0]        → Switch to workspace 1-10"
    echo "  Super + Shift + [1-9,0] → Move window to workspace 1-10"
    grep "^bind.*special:scratchpad\|togglespecialworkspace" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, togglespecialworkspace, scratchpad/ → Toggle scratchpad/' | \
        sed 's/, movetoworkspace, special:scratchpad/ → Move to scratchpad/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo "  Super + Mouse Wheel    → Scroll workspaces"
    echo ""

    echo "🖱️  MOUSE BINDINGS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bindm" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bindm\s*=\s*//' | \
        sed 's/, mouse:272,/ + Left Click →/' | \
        sed 's/, mouse:273,/ + Right Click →/' | \
        sed 's/movewindow/ Move window/' | \
        sed 's/resizewindow/ Resize window/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "📸 SCREENSHOTS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bind.*Print" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, exec, grim - | wl-copy/ → Full screen to clipboard/' | \
        sed 's/, exec, grim -g "$(slurp)" - | wl-copy/ → Selection to clipboard/' | \
        sed 's/, exec, grim -g "$(slurp)" ~\/Pictures\/$(date +%Y%m%d_%H%M%S).png/ → Selection to file/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "🔊 AUDIO & MEDIA"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  XF86AudioRaiseVolume   → Volume up"
    echo "  XF86AudioLowerVolume   → Volume down"
    echo "  XF86AudioMute          → Mute toggle"
    echo "  XF86AudioMicMute       → Mic mute toggle"
    echo "  XF86MonBrightnessUp    → Brightness up"
    echo "  XF86MonBrightnessDown  → Brightness down"
    echo "  Super + Vol Up/Down    → Brightness up/down"
    echo "  XF86AudioPlay/Pause    → Play/pause"
    echo "  XF86AudioNext          → Next track"
    echo "  XF86AudioPrev          → Previous track"
    grep "^bind.*switch-audio.sh" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, exec, ~\/.config\/hypr\/scripts\/switch-audio.sh astro/ → Astro audio/' | \
        sed 's/, exec, ~\/.config\/hypr\/scripts\/switch-audio.sh airpods/ → AirPods audio/' | \
        sed 's/, exec, ~\/.config\/hypr\/scripts\/switch-audio.sh hdmi/ → HDMI audio/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    echo "🚪 SESSION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep "^bind.*\(exit\|reload\)" "$CONFIG" | \
        sed 's/$mainMod/Super/g' | \
        sed 's/bind[el]*\s*=\s*//' | \
        sed 's/, exit,/ → Exit Hyprland/' | \
        sed 's/, exec, hyprctl reload/ → Reload config/' | \
        awk -F'→' '{printf "  %-25s %s\n", $1, $2}'
    echo ""

    cat << 'FOOTER'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         Press Super + Shift + / again to close this help
FOOTER
}

# Generate output and display with zenity
OUTPUT=$(generate_keybinds)

zenity --text-info \
    --title="Hyprland Keybindings" \
    --width=900 \
    --height=700 \
    --font="monospace 11" \
    --no-wrap \
    --filename=<(echo "$OUTPUT") &

# Store PID for cleanup
echo $! > /tmp/hypr-keybinds.pid
