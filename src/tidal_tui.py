import os
import sys
import subprocess
import json
import logging
import tidalapi
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import ListView, ListItem, Static, Label
from textual.binding import Binding
from textual.reactive import reactive

###############################################################################
# Setup logging (optional; you can remove if you don't need logs)
###############################################################################
if os.path.exists("tidal_tui.log"):
    open("tidal_tui.log", "w").close()

logging.basicConfig(
    filename="tidal_tui.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("=== Starting Tidal TUI Session ===")

###############################################################################
# TIDAL Session init or load from credentials.json
###############################################################################
session = tidalapi.Session()

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def load_or_login():
    """Load or login to TIDAL. Uses credentials.json if available."""
    try:
        with open("credentials.json", "r") as f:
            data = json.load(f)
            session.load_oauth_session(
                data["token_type"],
                data["access_token"],
                data["refresh_token"]
            )
    except FileNotFoundError:
        clear()
        session.login_oauth_simple()
        if session.check_login():
            data = {
                "token_type": session.token_type,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token
            }
            with open("credentials.json", "w") as f:
                json.dump(data, f)
            print("\n✅ Login successful!")
        else:
            print("❌ Error logging in.")
            sys.exit(1)

###############################################################################
# Models
###############################################################################
class PlaylistItem:
    """Wrapper around tidalapi.Playlist"""
    def __init__(self, tidal_playlist: tidalapi.Playlist):
        self.id = tidal_playlist.id
        self.name = tidal_playlist.name
        self.description = tidal_playlist.description or ""
        self.num_tracks = tidal_playlist.num_tracks

class TrackItem:
    """Wrapper around tidalapi.Track"""
    def __init__(self, tidal_track: tidalapi.Track):
        self.id = tidal_track.id
        self.name = tidal_track.name
        self.artist = tidal_track.artist.name
        self.duration = tidal_track.duration
        self.album_name = tidal_track.album.name
        self.url = tidal_track.get_url()

###############################################################################
# TUI Widgets for displaying playlists and tracks
###############################################################################
class PlaylistSection(Vertical):
    """Displays the list of playlists."""
    def __init__(self, playlists: List[PlaylistItem]):
        super().__init__()
        self.playlists = playlists

    def compose(self) -> ComposeResult:
        yield Static("Playlists", id="playlist-title")
        items = [ListItem(Label(pl.name)) for pl in self.playlists]
        yield ListView(*items)

class TrackSection(Vertical):
    """Displays the list of tracks for a chosen playlist."""
    def __init__(self, tracks: List[TrackItem]):
        super().__init__()
        self.tracks = tracks

    def compose(self) -> ComposeResult:
        yield Static("Tracks", id="tracks-title")
        items = [ListItem(Label(f"{t.name} - {t.artist}")) for t in self.tracks]
        yield ListView(*items)

class PlayerBar(Static):
    """Displays the currently playing track and handles playback."""
    playing = reactive(False)
    current_track: Optional[TrackItem] = None
    process: Optional[subprocess.Popen] = None

    def render(self) -> str:
        status = "▶" if self.playing else "⏸"
        track_info = (
            f"{self.current_track.name} - {self.current_track.artist}"
            if self.current_track
            else "No track playing"
        )
        return f"Now Playing\n{status} {track_info}"

    def play(self, track: TrackItem):
        """Launch mpv with the given track URL."""
        if self.process:
            self.process.kill()
        self.current_track = track
        try:
            self.process = subprocess.Popen(f"mpv '{track.url}'", shell=True)
            self.playing = True
        except Exception as e:
            logging.error(f"Failed to start track: {e}")

    def toggle(self):
        """Pause/Resume by killing mpv or restarting it."""
        if self.process:
            if self.playing:
                self.process.kill()
                self.playing = False
            else:
                self.play(self.current_track)

###############################################################################
# Main TUI Application
###############################################################################
class TidalTUI(App):
    """Main TIDAL TUI application."""
    CSS = """
    * {
        background: transparent;
    }

    #playlist-title, #tracks-title {
        background: transparent;
        color: green;
    }
    ListItem {
        color: white;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_play", "Play/Pause"),
        Binding("enter", "select", "Select"),
    ]

    def __init__(self):
        super().__init__()
        load_or_login()
        if not session.check_login():
            print("Authentication failed. Exiting.")
            sys.exit(1)

        self.playlists: List[PlaylistItem] = []
        self.tracks: List[TrackItem] = []
        self.player_process: Optional[subprocess.Popen] = None

        self.refresh_playlists()

    def compose(self) -> ComposeResult:
        yield Static("TIDAL TUI", id="app-title")
        yield Container(
            PlaylistSection(self.playlists),
            TrackSection(self.tracks),
            id="main-body"
        )
        yield PlayerBar()

    def refresh_playlists(self):
        """Load and store user playlists."""
        logging.info("Loading user playlists...")
        raw_pls = session.user.playlists()
        self.playlists = [PlaylistItem(pl) for pl in raw_pls]

    def action_toggle_play(self) -> None:
        """Handle Space -> toggle play."""
        player = self.query_one(PlayerBar)
        player.toggle()

    def action_select(self) -> None:
        """Handle Enter -> select either a playlist or a track."""
        focused = self.focused
        if isinstance(focused, ListView):
            index = focused.highlighted
            parent = focused.parent

            # If we're in the playlist section
            if isinstance(parent, PlaylistSection):
                if index is not None and index < len(self.playlists):
                    chosen_pl = self.playlists[index]
                    logging.info(f"Selected playlist: {chosen_pl.name}, ID: {chosen_pl.id}")

                    # Load tracks from TIDAL
                    tracks_list = session.playlist(chosen_pl.id).tracks(limit=25)
                    new_tracks = [TrackItem(t) for t in tracks_list]
                    self.tracks = new_tracks

                    # Update the UI
                    main_body = self.query_one("#main-body")
                    old_track_section = self.query(TrackSection).first()
                    if old_track_section:
                        old_track_section.remove()

                    new_track_section = TrackSection(self.tracks)
                    main_body.mount(new_track_section)

                    # Focus the track list
                    track_listview = new_track_section.query_one(ListView)
                    if track_listview:
                        track_listview.focus()

            # If we're in the track section
            elif isinstance(parent, TrackSection):
                if index is not None and index < len(self.tracks):
                    chosen_track = self.tracks[index]
                    player = self.query_one(PlayerBar)
                    player.play(chosen_track)

    def on_unmount(self) -> None:
        """Kill mpv on exit."""
        player = self.query_one(PlayerBar)
        if player.process:
            try:
                player.process.kill()
            except Exception as e:
                logging.error(f"Error killing mpv process: {e}")


if __name__ == "__main__":
    app = TidalTUI()
    app.run() 