#!/bin/bash
# Capture a screen selection, rsync to archie:/tmp/claude-ss/, copy remote path to clipboard

REMOTE="archie"
DIR="/tmp/claude-ss"
UUID=$(uuidgen)
FILE="$UUID.png"
LOCAL="$DIR/$FILE"
REMOTE_PATH="$DIR/$FILE"

# Clear and recreate dirs locally and on remote
rm -rf "$DIR"
mkdir -p "$DIR"
ssh "$REMOTE" "rm -rf $DIR && mkdir -p $DIR"

# Capture selection (slurp exits non-zero if cancelled)
if ! grim -g "$(slurp)" "$LOCAL"; then
    exit 1
fi

# Sync to remote
RSYNC_ERR=$(rsync "$LOCAL" "$REMOTE:$REMOTE_PATH" 2>&1)
if [ $? -ne 0 ]; then
    dunstify -a "Screenshot" -u critical -t 5000 "rsync failed" "$RSYNC_ERR"
    exit 1
fi

# Copy remote path to clipboard
printf '%s' "$REMOTE_PATH" | wl-copy

dunstify -a "Screenshot" -t 2000 "Screenshot saved" "$REMOTE_PATH"
