# Alt Command

A GTK 4 / libadwaita GNOME app with one toggle. Works on Wayland and X11 using
[keyd](https://github.com/rvaiya/keyd), a system-wide input remapper.

| Shortcut | Output | Result |
| --- | --- | --- |
| Left Alt+C | Ctrl+C | Copy |
| Left Alt+V | Ctrl+V | Paste |
| Left Alt+X | Ctrl+X | Cut |
| Left Alt+A | Ctrl+A | Select all |
| Left Alt+Z | Ctrl+Z | Undo |
| Left Alt+Shift+Z | Ctrl+Shift+Z | Redo |
| Left Alt+F | Ctrl+F | Find |
| Left Alt+S | Ctrl+S | Save |
| Left Alt+W | Alt+F4 | Close the focused window |
| Left Alt+Q | Ctrl+Q | Quit the application |
| Left Alt+Left | Home | Move to beginning of line |
| Left Alt+Right | End | Move to end of line |
| Left Alt+Shift+Right | Shift+End | Select to end of line |
| Left Alt+Shift+Left | Shift+Home | Select to beginning of line |

Alt+Left and Alt+Right replace application navigation shortcuts, such as browser
back/forward, with Home/End. Editors may interpret Home as the first non-whitespace
character or use their own behavior for wrapped lines.

Other Alt combinations, including Alt+Tab, remain Alt combinations. Right Alt
remains available for AltGr. The profile applies to **all keyboards and all
sessions**, persists across reboot, and stays enabled after closing the app.
Turning it off removes only this app's profile.

## Run

Dependencies: Python 3, PyGObject, GTK 4, libadwaita 1, polkit, systemd and keyd.
Ubuntu already provides the GUI dependencies on a standard GNOME installation.

```sh
git clone https://github.com/kamalgill/kg-alt-command.git
cd kg-alt-command
/usr/bin/python3 install-local.py
/usr/bin/python3 ~/.local/share/alt-command/app.py
```

Launch **Alt Command** from GNOME's app search. First enable asks for an
administrator password, installs the distribution's `keyd` package on Ubuntu /
Debian, and installs a root-owned backend in `/usr/local/libexec`. On other
distributions, install keyd with your package manager first. Each toggle uses
polkit authentication; the app does not store credentials or grant passwordless
access to keyboard remapping.

Ubuntu/Debian's `keyd.rvaiya` executable and upstream's `keyd` executable are
both supported. After an app update, the next enable automatically refreshes
the root-owned backend through the same administrator prompt.

The backend refuses to overwrite modified profiles or coexist with other keyd
`.conf` files, since competing device matches can silently prevent remapping.
Errors restore the previous profile. The UI reports success only after the
backend finishes, and restores the switch after cancelled authentication.

## Application behavior

Copy and paste use the usual Linux desktop bindings. In terminals, Ctrl+C often
interrupts and Ctrl+V has another meaning; terminal copy/paste commonly requires
Ctrl+Shift+C/V. Alt+Shift+C/V supplies those combinations. Applications with
custom bindings or editors that intercept Shift+Home/End may behave differently.
Use a US/QWERTY layout for the documented C/V physical key mappings.
Added letter shortcuts replace those Alt menu shortcuts. Redo follows the
GNOME convention; some apps use Ctrl+Y instead.
Alt+W closes the entire focused window, including in applications with tabs.
Alt+Q follows the application's Ctrl+Q binding; applications without that binding
may not quit. Normal save prompts and application-specific close handling apply.

## Recovery and removal

Disable the toggle before removing the app. If necessary, use:

```sh
sudo /usr/bin/python3 /usr/local/libexec/alt-command-backend disable
```

keyd's emergency sequence is Backspace+Escape+Enter; it stops the daemon. A reboot
reapplies an enabled profile, so remove the profile to disable it permanently.

After disabling, remove `~/.local/share/alt-command`,
`~/.local/share/applications/io.github.altcommand.App.desktop`, and the root-owned
`/usr/local/libexec/alt-command-backend`. keyd is left installed for other uses.

## Validation

```sh
/usr/bin/python3 -m unittest discover -s tests -v
```

The bindings and modifier passthrough are also checked against upstream
keyd v2.5.0's real input/output test harness. Live input remapping requires
administrator setup and manual testing in the target applications.

To reproduce the input/output checks (requires a C compiler and Git):

```sh
git clone --depth 1 --branch v2.5.0 https://github.com/rvaiya/keyd.git .validation/keyd
/usr/bin/python3 tests/run_keyd_tests.py .validation/keyd
```

GitHub Actions runs backend tests and all keyboard fixtures against the pinned
keyd v2.5.0 source commit. Tests do not install a daemon or change keyboard input.
