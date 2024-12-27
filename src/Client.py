import pytermgui as ptg
from api import initialize_session, get_playlists

# ANSI escape codes for colors
HOT_PINK_TEXT = "\033[38;5;199m"  # Bright hot pink
RESET = "\033[0m"
NO_BG = "\033[49m"  # Reset background to default

def run_tui():
    # Initialize Tidal session
    session = initialize_session()

    # Fetch playlists
    playlists = get_playlists(session)

    # Create a TUI manager
    with ptg.WindowManager() as manager:
        # State variables
        current_pane = 0
        selected_index = [0, 0, 0]  # For each pane

        # Function to create a styled label
        def create_label(label, width=30):
            # Add leading spaces to simulate left alignment
            padded_label = f"{NO_BG}{HOT_PINK_TEXT}{label.ljust(width)}{RESET}"
            return ptg.Label(padded_label)

        # Function to update label appearance
        def update_label_appearance(pane, index):
            for i, label in enumerate(pane):
                if i == index:
                    label.value = f"{HOT_PINK_TEXT}{label.value.strip()}{RESET}"
                else:
                    label.value = f"{NO_BG}{HOT_PINK_TEXT}{label.value.strip().ljust(30)}{RESET}"

        # Left Pane: Playlists
        playlist_labels = [create_label(playlist.name) for playlist in playlists]
        playlist_box = ptg.Window(
            ptg.Label("[210 bold]Playlists"),
            *playlist_labels,
            box="SINGLE",  # Add box style
            title="[210 bold]Navigation",
            padding=(0, 0),  # Remove padding
            parent_align=0  # Align to the left
        )

        # Middle Pane: Tracks
        track_labels = [create_label("Track 1"), create_label("Track 2")]  # Example tracks
        track_box = ptg.Window(
            ptg.Label("[bold]Tracks[/bold]"),
            *track_labels,
            box="SINGLE",  # Add box style
            parent_align=0,
            padding=(0, 0)  # Remove padding
        )

        # Right Pane: Play Queue
        play_queue_labels = [create_label("Queue Item 1"), create_label("Queue Item 2")]
        play_queue_box = ptg.Window(
            ptg.Label("[bold]Play Queue[/bold]"),
            *play_queue_labels,
            box="SINGLE",  # Add box style
            parent_align=0,
            padding=(0, 0)  # Remove padding
        )

        panes = [playlist_labels, track_labels, play_queue_labels]

        # Function to switch panes
        def switch_pane():
            nonlocal current_pane
            current_pane = (current_pane + 1) % len(panes)
            update_label_appearance(panes[current_pane], selected_index[current_pane])

        # Function to move selection up
        def move_up():
            nonlocal selected_index
            selected_index[current_pane] = max(0, selected_index[current_pane] - 1)
            update_label_appearance(panes[current_pane], selected_index[current_pane])

        # Function to move selection down
        def move_down():
            nonlocal selected_index
            selected_index[current_pane] = min(len(panes[current_pane]) - 1, selected_index[current_pane] + 1)
            update_label_appearance(panes[current_pane], selected_index[current_pane])

        # Function to select item
        def select_item():
            index = selected_index[current_pane]
            label = panes[current_pane][index]
            # Perform action on select

        # Add windows to the manager
        manager.add(playlist_box, track_box, play_queue_box)

        # Key bindings
        manager.bind("tab", switch_pane)
        manager.bind("up", move_up)
        manager.bind("down", move_down)
        manager.bind("enter", select_item)

        # Initial selection
        update_label_appearance(panes[current_pane], selected_index[current_pane])

        # Run the TUI
        manager.run()

if __name__ == "__main__":
    run_tui()