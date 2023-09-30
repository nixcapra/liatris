![](https://github.com/nixcapra/liatris/blob/main/media/icons/icon_256.png)
# Liatris
Liatris is a simple to-do app that I created for myself some time ago. I originally wrote this as part of another project and have now decided to open-source it. Please note that it lacks many features that are considered essential in most to-do apps, such as cloud syncing. Additionally, it utilizes its own database model and is not compatible with anything else. Liatris was loosely inspired by other to-do apps, like [Things](https://culturedcode.com/things/).

# Screenshot
![](https://github.com/nixcapra/liatris/blob/main/media/screenshots/adw_light_1.png)
[More screenshots here](https://github.com/nixcapra/liatris/tree/main/media/screenshots)

# Features
- Tasks are ordered by project.
- Each task has its own notes section.
- The app features a simple and easily configurable deadline system.
- There is a logbook where you can view completed tasks.
- The app does not connect to the internet.

# Usage
>Currently, Liatris does not have packages available for any distribution. I will likely create packages for Debian and possibly make a Flatpak or AppImage available in the future. However, you can still run it in its current state.

Install the following on Debian 12:

    sudo apt install python3-gi python-gi-dev python3-sqlalchemy python3-sqlalchemy-utils

Then run:

    python3 liatris.py
    
# Improving

I am generally open and grateful for contributions, but please understand that I may not be able to respond to pull requests (PRs) promptly. If you wish to report a bug, I am also appreciative. However, please be aware that I will disregard any theming bugs that I cannot reproduce on Adwaita.

Additionally, please note that there are many other impressive to-do apps for GNOME available, which may or may not deserve your attention more than mine.

### Things that i want to do in the future:

- Clean up and compartmentalize liatris.py.
- Make packages available, primarily .deb, Flatpak, and/or AppImage.
- Port the GUI to Gtk4 and libadw.
- ✔ Improve the logo. 
- Add XDG desktop integration.
- Implement a feature to export and import data.
- Generally enhance the code quality.
