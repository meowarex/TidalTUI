import tidalapi
import json
import warnings
import os
from dataclasses import dataclass
from typing import List, Optional
import subprocess
import sys

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
            print(f"\nFetching playlist: {playlist_id}")
            playlist = self.session.playlist(playlist_id)
            
            if not playlist:
                print("Error: Could not fetch playlist")
                return []
            
            print("Getting tracks from playlist...")
            playlist_tracks = playlist.tracks()
            
            if not playlist_tracks:
                print("Error: No tracks found in playlist")
                return []
            
            tracks = []
            for t in playlist_tracks:
                try:
                    track = Track(
                        id=str(t.id),
                        title=t.name,
                        artist=t.artist.name,
                        duration=t.duration,
                        album=t.album.name,
                        url=t.get_url()
                    )
                    tracks.append(track)
                    print(f"Added track: {track.title} by {track.artist}")
                except Exception as e:
                    print(f"Failed to load track: {e}")
            
            print(f"Successfully loaded {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            import traceback
            print(f"Error loading playlist: {e}")
            print(traceback.format_exc())
            return []

    def play_track(self, track_url: str):
        try:
            process = subprocess.Popen(f"mpv '{track_url}'", shell=True)
            return process
        except Exception as e:
            print(f"Error playing track: {e}")
            return None 