import pytermgui as ptg
from api import initialize_session, get_playlists

def run_tui():
    # Initialize Tidal session
    session = initialize_session()

    # Fetch playlists
    playlists = get_playlists(session)

    # Create a TUI manager
    with ptg.WindowManager() as manager:
        # Left Pane: Playlists
        playlist_box = ptg.Window(
            ptg.Label("[210 bold]Playlists"),
            *[ptg.Label(playlist.name, parent_align=0) for playlist in playlists],
            box="SINGLE",
            align="left"
        ).set_title("[210 bold]Navigation")

        # Middle Pane: Tracks
        track_box = ptg.Window(
            ptg.Label("[bold]Tracks[/bold]"),
            box="SINGLE",
            align="left"
        )

        # Right Pane: Play Queue
        play_queue_box = ptg.Window(
            ptg.Label("[bold]Play Queue[/bold]"),
            ptg.Label("No tracks in queue"),
            box="SINGLE"
        )

        # Lyrics Tab
        lyrics_box = ptg.Window(
            ptg.Label("[bold]Lyrics[/bold]"),
            box="SINGLE"
        )

        # Add windows to the manager
        manager.add(playlist_box, track_box, play_queue_box)

        # Function to switch to lyrics tab
        def show_lyrics():
            manager.remove(play_queue_box)
            manager.add(lyrics_box)

        # Function to switch back to play queue
        def show_play_queue():
            manager.remove(lyrics_box)
            manager.add(play_queue_box)

        # Example key bindings to switch tabs
        manager.bind("l", show_lyrics)
        manager.bind("q", show_play_queue)

        # Run the TUI
        manager.run()
