#!/usr/bin/python3
"""Install the launcher for the current user; privileged setup happens in the app."""
from pathlib import Path
import shutil

source = Path(__file__).resolve().parent
destination = Path.home() / '.local/share/alt-command'
destination.mkdir(parents=True, exist_ok=True)
for name in ('app.py', 'backend.py'):
    shutil.copyfile(source / name, destination / name)
applications = Path.home() / '.local/share/applications'
applications.mkdir(parents=True, exist_ok=True)
(applications / 'io.github.altcommand.App.desktop').write_text(f'''[Desktop Entry]
Type=Application
Name=Alt Command
Comment=Toggle Mac-style Alt shortcuts
Exec=/usr/bin/python3 "{destination}/app.py"
Icon=input-keyboard
Terminal=false
Categories=Utility;GTK;
Keywords=Keyboard;Alt;Command;Copy;Paste;
StartupNotify=true
''')
print(f'Installed Alt Command: {destination}')
