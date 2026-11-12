# PyMon

## Info
DISCLAIMER: This app only works on hyprland on the newer versions that already use lua. **release>=0.55**
This app uses python 3.13.8.

## Setup
Follow this short tutorial to install PyMon:
1. Install uv. If already installed, skip this step. (You can also use other package installers but this tutorial wont work.)
2. Navigate into the folder you downloaded the code to.
3. Run ```uv python install 3.13```
4. Run ```uv python pin 3.13```
5. Run ```uv sync```
6. Done
7. To run the program, just do ```uv run Main.py``` in the same directory

In addition to that you can also add the program to your application launcher.
For that follow these steps:
1. Navigate to ```~/.local/share/applications/```
2. In the ```PyMon.desktop``` file, rewrite it to match the save path of the program and your user
4. Add the ```PyMon.desktop``` file to the path above
5. If the program doesn't show up: Run ```update-desktop-database ~/.local/share/applications```
6. If that command doesn't exist: Run ```sudo pacman -S desktop-file-utils``` and try again
7. Done
