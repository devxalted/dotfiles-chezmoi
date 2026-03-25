#!/usr/bin/env python3
"""Save/remove currently playing Spotify track to/from Liked Songs, or add to a playlist"""

import subprocess
import json
import sys
import tempfile
import urllib.request
from pathlib import Path
import tekore as tk

CONFIG_DIR = Path.home() / ".config" / "spotify"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

def notify(title, body, urgency="normal", icon=None):
    """Send desktop notification"""
    cmd = [
        "dunstify",
        "-a", "Spotify",
        "-u", urgency,
        "-h", "string:x-dunst-stack-tag:spotify-like",
        "-t", "3000",
    ]
    if icon:
        cmd += ["-I", icon]
    cmd += [title, body]
    subprocess.run(cmd)

def get_track_id():
    """Get Spotify track ID from playerctl metadata"""
    try:
        result = subprocess.run(
            ["playerctl", "-p", "spotify", "metadata", "mpris:trackid"],
            capture_output=True,
            text=True,
            check=True
        )
        trackid = result.stdout.strip()
        # Extract ID from: /org/mpris/MediaPlayer2/spotify/track/TRACK_ID
        if "spotify" in trackid:
            return trackid.split("/")[-1]
        return None
    except subprocess.CalledProcessError:
        return None

def get_track_info():
    """Get track title and artist for display"""
    try:
        title = subprocess.run(
            ["playerctl", "-p", "spotify", "metadata", "title"],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        artist = subprocess.run(
            ["playerctl", "-p", "spotify", "metadata", "artist"],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        return f"{title} - {artist}"
    except subprocess.CalledProcessError:
        return "Unknown Track"

def get_album_art():
    """Download album art and return path to temp file"""
    try:
        art_url = subprocess.run(
            ["playerctl", "-p", "spotify", "metadata", "mpris:artUrl"],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        if not art_url:
            return None

        art_path = Path(tempfile.gettempdir()) / "spotify-album-art.jpg"
        urllib.request.urlretrieve(art_url, art_path)
        return str(art_path)
    except (subprocess.CalledProcessError, Exception):
        return None

def get_spotify_client():
    """Get authenticated Spotify API client with token caching"""
    if not CREDENTIALS_FILE.exists():
        notify("Spotify Setup Required",
               "Create credentials.json in ~/.config/spotify/",
               "critical")
        return None

    with open(CREDENTIALS_FILE) as f:
        creds = json.load(f)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Create credentials object
    cred = tk.Credentials(creds["client_id"], creds["client_secret"], creds["redirect_uri"])

    # Load or obtain refresh token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            refresh_token = json.load(f)["refresh_token"]
    else:
        # First time: manual OAuth flow (one-time setup)
        scope = (
            tk.scope.user_library_modify
            + tk.scope.user_library_read
            + tk.scope.user_read_currently_playing
            + tk.scope.playlist_read_private
            + tk.scope.playlist_modify_public
            + tk.scope.playlist_modify_private
        )
        auth_url = cred.user_authorisation_url(scope)

        subprocess.run(["xdg-open", auth_url], check=False)

        print("=" * 60)
        print("SPOTIFY AUTHENTICATION")
        print("=" * 60)
        print()
        print("1. Authorize in the browser that just opened")
        print("2. You'll see 'Unable to connect' - THIS IS NORMAL")
        print("3. Copy the FULL URL from your browser address bar")
        print()
        callback_url = input("Paste the callback URL here: ").strip()

        if "code=" not in callback_url:
            notify("Authentication Failed", "Invalid callback URL", "critical")
            return None

        code = callback_url.split("code=")[1].split("&")[0]
        user_token = cred.request_user_token(code)
        refresh_token = user_token.refresh_token

        # Cache refresh token for future use
        with open(TOKEN_FILE, 'w') as f:
            json.dump({"refresh_token": refresh_token}, f)
        TOKEN_FILE.chmod(0o600)
        print("Authentication successful! Token saved.")

    # Get a fresh access token using the refresh token
    token = cred.refresh_user_token(refresh_token)

    return tk.Spotify(token)

def get_playlists(spotify):
    """Fetch all user playlists, returning dict of display_name -> playlist_id"""
    playlists = {}
    seen_names = {}  # name -> (playlist_id, owner_display) for first occurrence
    for item in spotify.all_items(spotify.followed_playlists()):
        name = item.name
        pid = item.id
        owner = item.owner.display_name or item.owner.id
        if name in seen_names:
            first = seen_names[name]
            if first is not None:
                # Rename the first occurrence we saw
                del playlists[name]
                playlists[f"{name} (by {first[1]})"] = first[0]
                seen_names[name] = None  # mark as already disambiguated
            playlists[f"{name} (by {owner})"] = pid
        else:
            seen_names[name] = (pid, owner)
            playlists[name] = pid
    return playlists


def show_playlist_picker(playlists):
    """Show wofi picker with playlist names, return selected name or None"""
    names = "\n".join(sorted(playlists.keys()))
    result = subprocess.run(
        ["wofi", "--dmenu", "--insensitive", "--prompt", "Add to playlist:",
         "--width", "400", "--lines", "15", "--cache-file", "/dev/null"],
        input=names, capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    selected = result.stdout.strip()
    return selected if selected else None


def playlist_add_track(spotify, playlist_id, track_id, playlist_name):
    """Add track to playlist and show notification"""
    art = get_album_art()
    track_info = get_track_info()
    spotify.playlist_add(playlist_id, [f"spotify:track:{track_id}"])
    notify(f"Added to {playlist_name}", track_info, icon=art)


def main():
    """Like/unlike, playlist add, copy link, or show now playing"""
    unlike = "--unlike" in sys.argv
    playlist_mode = "--playlist" in sys.argv
    copy_link = "--copy-link" in sys.argv
    now_playing = "--now-playing" in sys.argv

    # Check if Spotify is running
    result = subprocess.run(
        ["playerctl", "-p", "spotify", "status"],
        capture_output=True
    )

    if result.returncode != 0:
        notify("Spotify Not Running", "Start Spotify and play a song", "normal")
        return

    # Get track info
    track_id = get_track_id()
    if not track_id:
        notify("Error", "Could not get current track", "critical")
        return

    # Modes that don't need the Spotify API
    if copy_link:
        url = f"https://open.spotify.com/track/{track_id}"
        subprocess.run(["wl-copy", url])
        track_info = get_track_info()
        art = get_album_art()
        notify("Copied Link", track_info, icon=art)
        return

    if now_playing:
        track_info = get_track_info()
        art = get_album_art()
        notify("Now Playing", track_info, icon=art)
        return

    if not playlist_mode:
        track_info = get_track_info()
        art = get_album_art()

    # Get authenticated client
    spotify = get_spotify_client()
    if not spotify:
        return

    try:
        if playlist_mode:
            playlists = get_playlists(spotify)
            if not playlists:
                notify("No Playlists", "No playlists found", "normal")
                return
            selected = show_playlist_picker(playlists)
            if not selected or selected not in playlists:
                return
            playlist_add_track(spotify, playlists[selected], track_id, selected)
        else:
            is_liked = spotify.saved_tracks_contains([track_id])[0]

            if unlike:
                if is_liked:
                    spotify.saved_tracks_delete([track_id])
                    notify("♡ Removed from Liked", track_info, icon=art)
                else:
                    notify("♡ Not in Liked Songs", track_info, icon=art)
            else:
                if is_liked:
                    notify("♥ Already Liked", track_info, icon=art)
                else:
                    spotify.saved_tracks_add([track_id])
                    notify("♥ Liked Song", track_info, icon=art)

    except Exception as e:
        notify("Spotify API Error", str(e), "critical")

if __name__ == "__main__":
    main()
