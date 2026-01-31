#!/bin/bash
# Audio output switcher for Hyprland

AIRPODS_MAC="90:9C:4A:DF:2E:D3"

# Function to find sink ID by name pattern
find_sink() {
    wpctl status | grep -A 50 "Sinks:" | grep "$1" | head -1 | awk '{print $2}' | sed 's/\.$//g'
}

# Function to get current volume as percentage
get_volume() {
    wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2 * 100)}'
}

# Function to connect AirPods if not connected
connect_airpods() {
    # Check if AirPods are connected
    if ! bluetoothctl info "$AIRPODS_MAC" 2>/dev/null | grep -q "Connected: yes"; then
        dunstify -a "Audio Output" -i "bluetooth" -t 2000 "Connecting..." "AirPods Max"
        bluetoothctl connect "$AIRPODS_MAC" >/dev/null 2>&1
        sleep 2  # Wait for connection to establish
    fi
}

# Function to send styled notification
send_notification() {
    local icon="$1"
    local device="$2"
    local volume=$(get_volume)

    dunstify -a "Audio Output" \
        -h string:x-dunst-stack-tag:audio-switch \
        -h int:value:"$volume" \
        -t 2000 \
        "$icon  Audio Output" \
        "$device"
}

case "$1" in
    "astro")
        SINK_ID=$(find_sink "Astro A50 Game")
        wpctl set-default "$SINK_ID"
        send_notification "🎧" "Astro A50 Gaming Headset"
        ;;
    "airpods")
        connect_airpods
        # Look for bluez_output in Filters section
        SINK_ID=$(wpctl status | grep "bluez_output" | awk '{print $2}' | sed 's/\.$//g')
        if [ -n "$SINK_ID" ]; then
            wpctl set-default "$SINK_ID"
            send_notification "🎧" "AirPods Max"
        else
            dunstify -a "Audio Output" -u critical -t 2000 "❌  Error" "AirPods Max not available"
        fi
        ;;
    "hdmi")
        SINK_ID=$(find_sink "HDMI")
        wpctl set-default "$SINK_ID"
        send_notification "🖥️" "HDMI Display Audio"
        ;;
    *)
        echo "Usage: $0 {astro|airpods|hdmi}"
        exit 1
        ;;
esac
