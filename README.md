# PyQt6 Card Grid Example

This is a simple example of a card grid UI built with PyQt6.

## Installation

To install the dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Usage

To run the application, execute the following command:

```bash
python main.py
```

## Todo

- [x] Implement a search bar that expands on selection.
- [x] Add an on-screen keyboard for text input.
- [x] Display dynamic search results in a 3x2 grid.
- [x] Enable full arrow key navigation between the keyboard and search results.
- [x] Ensure the search bar clears automatically upon exit.
- [x] Resize the main grid's selected rectangle to its original state when the search bar is active.
- [x] Add a card-like visual design to the keyboard keys.
- [x] Streamline the codebase for improved readability and maintainability.
- [x] Open mp4 video after selecting the right movie
- [x] Fix arrows so they work on video player
- [x] Fix back button so it works on video player
- [x] Have the pause/ffw/rw/back buttons not adjust the video display, but be overlayed
- [x] have those same buttons fade disapear after 3 seconds of no input from the user
- [x] A press from any of the arrow keys should make them appear and I should be on the pause button
- [x] Make it so the buttons don't disappear as long as it is paused
- [x] If I press enter it should pause the video.
- [x] Have the video player return to previous screen once the mp4 video is done playing
- [x] Add a animation for when the back button is pressed, or the mp4 video is done playing (its not pretty but its something)
- [x] Add the same animation (but reversed) for when I select a movie (its not pretty but its something)
- [x] Remove all mouse input code from both files, video_player and main
- [x] When the mp4 video opens up in video_player I want the button to be already disappeared by default
- [x] Make tiny change so that video truly goes full screen when the buttons disappear

- [ ] Have a program make mp4 videos that are 15 seconds long of each animal name just being displayed on the screen, white text on black background
- [ ] Create a way to store hundreds of mp4 files in an organized way
- [ ] Store each of those videos in their correct place
- [ ] Store the data of the timestamp I stopped the video at
- [ ] Store when each video was watched last
- [ ] Allow for sorting the movies based on when they were watched last
- [ ]
- [ ]
- [ ]
- [ ]
- [ ]
- [ ]
- [ ]
