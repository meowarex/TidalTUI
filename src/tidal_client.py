import tidalapi
import json
import warnings
import os
from dataclasses import dataclass
from typing import List, Optional
import subprocess
import sys
import logging

# Clear the log file if it exists
if os.path.exists('tidal_tui.log'):
    open('tidal_tui.log', 'w').close()

# Setup logging
logging.basicConfig(
    filename='tidal_tui.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("=== Starting new TidalTUI session ===")

def clear():
    os.system("clear" if os.name != 'nt' else "cls")

warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

@dataclass
class Track:
    id: str
    title: str
    artist: str
    duration: int
    album: str
    url: str

@dataclass
class Playlist:
    uuid: str
    title: str
    description: str
    number_of_tracks: int

class TidalClient:
    def __init__(self):
        self.session = tidalapi.Session()
        logging.info("Initializing TidalClient")
        self._load_or_login()

    def _load_or_login(self):
        try:
            with open('credentials.json', 'r') as f:
                data = json.load(f)
                self.session.load_oauth_session(
                    data["token_type"],
                    data["access_token"],
                    data["refresh_token"]
                )
        except FileNotFoundError:
            clear()
            self.session.login_oauth_simple()
            if self.session.check_login():
                data = {
                    "token_type": self.session.token_type,
                    "access_token": self.session.access_token,
                    "refresh_token": self.session.refresh_token
                }
                with open('credentials.json', 'w') as f:
                    json.dump(data, f)
                print("\n✅ Login successful!")
            else:
                print("❌ There was an error in the login section.")
                sys.exit(1)

    def check_auth(self) -> bool:
        return self.session.check_login()

    def get_playlists(self) -> List[Playlist]:
        playlists = []
        for pl in self.session.user.playlists():
            playlists.append(Playlist(
                uuid=pl.id,
                title=pl.name,
                description=pl.description or "",
                number_of_tracks=pl.num_tracks
            ))
        return playlists

    def get_tracks(self, playlist_id: str) -> List[Track]:
        try:
            logging.info(f"Fetching playlist: {playlist_id}")
            playlist = self.session.playlist(playlist_id)
            
            if not playlist:
                logging.error("Could not fetch playlist")
                return []
            
            logging.info("Getting tracks from playlist...")
            tracks_list = playlist.tracks(limit=25)  # Using same limit as working example
            
            tracks = []
            x = -1
            for name in tracks_list:
                x = x + 1
                try:
                    track = Track(
                        id=str(tracks_list[x].id),
                        title=tracks_list[x].name,
                        artist=tracks_list[x].artist.name,
                        duration=tracks_list[x].duration,
                        album=tracks_list[x].album.name,
                        url=tracks_list[x].get_url()
                    )
                    tracks.append(track)
                    logging.info(f"Added track: {track.title}")
                except Exception as e:
                    logging.error(f"Failed to load track: {e}")
            
            logging.info(f"Successfully loaded {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            logging.error(f"Error loading playlist: {e}")
            logging.error(traceback.format_exc())
            return []

    def play_track(self, track_url: str):
        try:
            process = subprocess.Popen(f"mpv '{track_url}'", shell=True)
            # Wait for process to complete or be killed
            while process.poll() is None:
                pass
            return process
        except Exception as e:
            logging.error(f"Error playing track: {e}")
            return None 