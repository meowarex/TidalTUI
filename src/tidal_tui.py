from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Static, Label
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from textual.widgets import Static
from textual.css.query import NoMatches

from rich.text import Text
from rich.style import Style

from tidal_client import TidalClient, Track, Playlist
import os
import asyncio
from typing import List, Optional
import subprocess

class TitleBar(Static):
    def compose(self) -> ComposeResult:
        yield Static("TIDAL", id="app-title")
        yield Static("Home Explore Library", id="nav-tabs")

    def on_mount(self) -> None:
        self.styles.height = 3
        self.styles.border = ("heavy", "white")
        self.styles.padding = (0, 1)

class PlaylistSection(Vertical):
    def __init__(self, playlists: List[Playlist]):
        super().__init__()
        self.playlists = playlists
        self.styles.border = ("heavy", "white")
        self.styles.width = "25%"

    def compose(self) -> ComposeResult:
        yield Static("Playlists", id="playlist-title")
        items = [ListItem(Label(playlist.title)) for playlist in self.playlists]
        yield ListView(*items)

class TrackSection(Vertical):
    def __init__(self, tracks: List[Track]):
        super().__init__()
        self.tracks = tracks
        self.styles.border = ("heavy", "white")
        self.styles.width = "75%"

    def compose(self) -> ComposeResult:
        yield Static("Tracks", id="tracks-title")
        items = [ListItem(Label(f"{track.title} - {track.artist}")) for track in self.tracks]
        yield ListView(*items)

class PlayerBar(Static):
    playing = reactive(False)
    current_track: Optional[Track] = None
    process: Optional[subprocess.Popen] = None

    def on_mount(self) -> None:
        self.styles.height = 3
        self.styles.border = ("heavy", "white")
        self.styles.padding = (0, 1)

    def render(self) -> str:
        status = "▶" if self.playing else "⏸"
        track_info = (
            f"{self.current_track.title} - {self.current_track.artist}"
            if self.current_track
            else "No track playing"
        )
        return f"Now Playing\n{status} {track_info}"

    def play(self, track: Track, client: TidalClient):
        if self.process:
            self.process.kill()
        self.current_track = track
        self.process = client.play_track(track.url)
        self.playing = True

    def toggle(self):
        if self.process:
            if self.playing:
                self.process.kill()
                self.playing = False
            else:
                self.play(self.current_track, self.app.client)

class TidalTUI(App):
    CSS = """
    * {
        background: transparent;
    }
    
    #app-title {
        dock: left;
        padding: 0 1;
        color: white;
    }
    
    #nav-tabs {
        dock: right;
        padding: 0 1;
        color: white;
    }
    
    #playlist-title {
        dock: top;
        padding: 0 1;
        height: 1;
        color: white;
    }
    
    #tracks-title {
        dock: top;
        padding: 0 1;
        height: 1;
        color: white;
    }
    
    ListView {
        height: 100%;
        color: white;
        scrollbar-color: white;
    }
    
    ListItem {
        padding: 0 1;
        color: white;
    }
    
    ListItem:hover {
        background: $boost;
    }
    
    PlayerBar {
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
        self.client = TidalClient()
        self.playlists: List[Playlist] = []
        self.tracks: List[Track] = []
        self.current_track: Optional[Track] = None
        self.player_process: Optional[subprocess.Popen] = None

    def on_mount(self) -> None:
        if not self.client.check_auth():
            self.exit("Authentication failed. Please restart the application and try logging in again.")
            return

        # Load initial playlists
        self.playlists = self.client.get_playlists()
        self.update_views()

    def update_views(self) -> None:
        main_container = self.query_one("#main")
        
        # Remove existing sections
        main_container.remove_children()
        
        # Add new sections
        main_container.mount(PlaylistSection(self.playlists))
        main_container.mount(TrackSection(self.tracks))

    def compose(self) -> ComposeResult:
        yield TitleBar()
        yield Container(
            PlaylistSection([]),
            TrackSection([]),
            id="main"
        )
        yield PlayerBar()

    def action_toggle_play(self) -> None:
        try:
            player = self.query_one(PlayerBar)
            player.toggle()
        except Exception:
            pass

    def action_select(self) -> None:
        focused = self.focused
        if isinstance(focused, ListView):
            selected = focused.highlighted
            if selected is not None:
                # Check if we're in the playlist section
                if isinstance(focused.parent, PlaylistSection):
                    try:
                        playlist = self.playlists[selected]
                        print("\n" + "="*50)
                        print(f"Selected playlist: {playlist.title}")
                        print(f"Playlist ID: {playlist.uuid}")
                        print(f"Number of tracks: {playlist.number_of_tracks}")
                        print("="*50)
                        
                        self.tracks = self.client.get_tracks(playlist.uuid)
                        
                        print(f"\nTrack loading complete. Got {len(self.tracks)} tracks")
                        for i, track in enumerate(self.tracks):
                            print(f"{i+1}. {track.title} - {track.artist}")
                        print("="*50 + "\n")
                        
                        # Update the track section
                        self.query_one(TrackSection).remove()
                        self.query_one("#main").mount(TrackSection(self.tracks))
                        
                        # Focus the new track list
                        self.query_one(TrackSection).query_one(ListView).focus()
                        
                    except Exception as e:
                        import traceback
                        print(f"\nError loading tracks: {e}")
                        print(traceback.format_exc())
                # Check if we're in the track section
                elif isinstance(focused.parent, TrackSection) and selected < len(self.tracks):
                    track = self.tracks[selected]
                    try:
                        player = self.query_one(PlayerBar)
                        player.play(track, self.client)
                        self.player_process = player.process
                    except Exception as e:
                        print(f"Error playing track: {e}")

    def on_unmount(self) -> None:
        # Clean up player process on exit
        if self.player_process:
            try:
                self.player_process.kill()
            except Exception:
                pass

if __name__ == "__main__":
    app = TidalTUI()
    app.run() 