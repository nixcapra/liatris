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
