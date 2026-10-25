# kamalt-command

A small GNOME app with one toggle: use the **left Alt key on a Windows keyboard
like the Command key on a Mac** for common editing, navigation, and application
shortcuts.

The interface uses Python, GTK 4, and libadwaita. Remapping is handled by
[keyd](https://github.com/rvaiya/keyd), which works below the desktop input stack
and supports both Wayland and X11. No GNOME Shell extension is required.

## Shortcut mappings

All shortcuts below use **left Alt**. Right Alt remains available for AltGr.

| Shortcut | Linux key sequence emitted | Action |
| --- | --- | --- |
| Alt+C | Ctrl+C | Copy |
| Alt+V | Ctrl+V | Paste |
| Alt+X | Ctrl+X | Cut |
| Alt+A | Ctrl+A | Select all |
| Alt+Z | Ctrl+Z | Undo |
| Alt+Shift+Z | Ctrl+Shift+Z | Redo |
| Alt+F | Ctrl+F | Find |
| Alt+S | Ctrl+S | Save |
| Alt+W | Alt+F4 | Close the entire focused window |
| Alt+Q | Ctrl+Q | Quit the application, where supported |
| Alt+Left | Home | Move to the beginning of the current line |
| Alt+Right | End | Move to the end of the current line |
| Alt+Up | Ctrl+Home | Move to the top of the page/document |
| Alt+Down | Ctrl+End | Move to the bottom of the page/document |
| Alt+Shift+Left | Shift+Home | Select from the cursor to the beginning of the line |
| Alt+Shift+Right | Shift+End | Select from the cursor to the end of the line |

Holding Shift also carries through to the ordinary letter mappings. For example,
Alt+Shift+C and Alt+Shift+V emit Ctrl+Shift+C and Ctrl+Shift+V, which commonly copy
and paste in terminals.

Unlisted combinations retain Alt behavior, including Alt+Tab, Alt+Shift+Tab, and
Alt+F4. The physical Ctrl and Windows/Super keys retain their usual functions.

### Differences and application behavior

- **Alt+W closes a window, not just a tab.** This intentionally emits GNOME's
  Alt+F4 rather than Ctrl+W. The application handles unsaved-change prompts.
- **Alt+Q is an application shortcut, not a forced termination.** Applications
  without a Ctrl+Q quit binding may ignore it or perform another action.
- **Alt+Left/Right replace browser back/forward shortcuts.** When enabled, these
  keys emit Home/End in every application.
- **Home/End behavior depends on the editor.** Some editors move Home to the
  first non-whitespace character; wrapped-line behavior may also differ.
- **Alt+Up/Down use Ctrl+Home/End.** Browsers generally scroll to the top/bottom;
  editors move the cursor to the beginning/end of the document. This replaces
  existing Alt+Up/Down actions such as navigating to a parent folder.
- **Terminals use different bindings.** Alt+C emits Ctrl+C, which usually
  interrupts a process. Use Alt+Shift+C/V for terminal copy/paste. Other mappings,
  such as Alt+Q or Alt+S, also follow the terminal's Ctrl-key behavior.
- **Redo varies.** The app emits the GNOME convention Ctrl+Shift+Z. Applications
  that require Ctrl+Y need their own shortcut adjustment.
- **Alt menu accelerators are replaced for mapped keys.** For example, Alt+F
  becomes Find instead of opening an application's File menu.
- **Keyboard layouts matter.** The documented letter mappings assume a
  US/QWERTY layout. keyd handles physical key codes; non-QWERTY layouts have not
  been validated.

## Supported systems and requirements

### Tested environment

The app was built and exercised on the following system. This is the currently
validated desktop environment, not a claim that every GNOME or Linux version
has been tested.

| Component | Tested version |
| --- | --- |
| Distribution | Ubuntu 26.04.1 LTS |
| Desktop | GNOME Shell 50.1 |
| Display session | Wayland |
| Linux kernel | 7.0.0-38-generic |
| Python | 3.14.4 (`/usr/bin/python3`) |
| PyGObject | 3.56.2 |
| GTK | 4.22.4 |
| libadwaita | 1.9.1 |
| keyd | 2.5.0; Ubuntu package 2.5.0-5 |

### Compatibility outside the tested environment

The app does not call GNOME Shell APIs or depend on a particular Shell extension
version. Other GNOME versions can be compatible if the requirements below are
present, but no broader GNOME version range has been certified.

| Requirement | Details |
| --- | --- |
| Operating system | Native Linux installation with evdev and uinput access |
| Service manager | systemd; the backend uses `systemctl` and `keyd.service` |
| Python | Python 3; use a current distribution Python, preferably 3.10 or newer |
| GUI bindings | PyGObject with GTK 4 and Adw 1 introspection data |
| libadwaita | 1.2 or newer; the app uses `Adw.MessageDialog` |
| GTK | GTK 4, at the version required by the installed libadwaita package |
| Remapping service | keyd 2.5.0 is validated; other releases are untested |
| Authentication | `/usr/bin/pkexec`, polkit, and a desktop authentication agent |
| Administrative access | Required to install/update the backend and toggle the profile |

The libadwaita floor follows the documented
[`Adw.MessageDialog` availability since 1.2](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/1.2/class.MessageDialog.html).

- **Wayland:** validated locally on GNOME.
- **X11:** supported by keyd's input architecture, but not tested end to end here.
- **Other Linux distributions:** expected to be compatible when the requirements
  and executable paths are available. Install keyd and GUI dependencies with
  your distribution's package manager first.
- **Other desktops:** may work with GTK/libadwaita and polkit installed, but have
  not been validated.
- **Ubuntu/Debian:** automatic first-time keyd installation uses `apt-get` only
  when the executable is absent and the package is available in enabled repos.
- **Older libadwaita releases:** versions before 1.2 are not supported.
- **Windows, macOS, containers, and sandboxed packaging:** not supported targets.
  The app needs access to the host's keyboard service; no Flatpak/Snap packaging
  is provided.

Both executable names are supported: Ubuntu/Debian's `keyd.rvaiya` and upstream's
`keyd`. The app searches standard system executable directories.

## Install the Debian package (recommended for Ubuntu/Debian)

Download `kamalt-command_0.1.2_all.deb` from
[GitHub Releases](https://github.com/kamalgill/kamalt-command/releases/latest).
From the directory containing the downloaded file:

```sh
sudo apt install ./kamalt-command_0.1.2_all.deb
kamalt-command
```

APT resolves the declared dependencies from your configured repositories:
Python 3.10+, PyGObject, GTK 4, libadwaita 1.2+, pkexec, polkitd, systemd,
and keyd 2.5.0+. If keyd is unavailable in those repositories, APT will report
an unsatisfied dependency; use the source-install route below after installing
keyd separately. Do not force installation with missing dependencies.

The package is `Architecture: all` because the app is Python; native dependencies
still must exist for your architecture. The package has been validated through
archive extraction, simulated removal/upgrade tests, an APT installation dry
run on the Ubuntu 26.04.1 desktop, and a real APT install/remove check in an
isolated Ubuntu 26.04 container. Live desktop installation/removal across other
Linux releases has not been certified.

Installing the app does not automatically enable its remapping profile. Open
**kamalt-command**, turn the toggle on, and authenticate. If you already had an
enabled source-install profile, that profile remains enabled. The package can
manage the same existing profile.

### Switching from a source installation

Install the `.deb` first and close the old app. Your per-user launcher can shadow
the package's launcher. Remove the old launcher's desktop file to use the packaged
app from GNOME search:

```sh
rm -f ~/.local/share/applications/io.github.altcommand.App.desktop
kamalt-command
```

After confirming the packaged app works, you can remove the old per-user files
and source-install backend:

```sh
rm -r ~/.local/share/alt-command
sudo rm -f /usr/local/libexec/alt-command-backend
```

Keep `/etc/keyd/alt-command.conf`; both installation methods use it. There is no
need to delete your cloned source repository.

### Package updates and removal

For an update, download the new `.deb` and install it with `sudo apt install ./...`.
GitHub release downloads do not configure an APT repository or automatic updates.
Restart the app and toggle off/on to apply any changed mappings. Package upgrades
preserve the current profile.

To remove the package:

```sh
sudo apt remove kamalt-command
```

Removal disables and reloads the app's managed profile before deleting its
backend. It leaves keyd installed and does not stop keyd or remove other profiles.
If the profile was manually edited, or reloading fails, removal reports an error
instead of silently deleting custom configuration. Resolve the reported problem
and retry. If the profile is already absent, removal needs no keyboard reload.

## Install from source (alternative)

### 1. Install GUI dependencies

On Ubuntu/Debian:

```sh
sudo apt-get update
sudo apt-get install git python3 python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 pkexec polkitd
```

Check that your libadwaita version meets the requirement above. Standard GNOME
installations may already include these dependencies. On other distributions,
install the equivalent packages and keyd using your package manager.

To check availability of the keyd package on Ubuntu/Debian:

```sh
apt-cache policy keyd
```

If there is no candidate, install keyd following its
[upstream instructions](https://github.com/rvaiya/keyd#installation) before
turning on the app. Do not substitute an unrelated similarly named package.

### 2. Clone and install the app launcher

```sh
git clone https://github.com/kamalgill/kamalt-command.git
cd kamalt-command
/usr/bin/python3 install-local.py
```

The local installer runs as your ordinary user. It copies the app into your
home directory and adds a GNOME application launcher. No compilation, virtual
environment, or pip installation is needed.

The repository's visibility and your GitHub access determine whether cloning
requires authentication.

### 3. Open kamalt-command

Search for **kamalt-command** in GNOME's application overview, or run:

```sh
/usr/bin/python3 ~/.local/share/alt-command/app.py
```

Use `/usr/bin/python3` rather than a pyenv or virtual-environment interpreter,
so the distribution's PyGObject bindings are available.

### 4. Turn the toggle on

Complete the administrator authentication prompt. First-time setup:

1. Installs the distribution's keyd package on apt-based systems if needed.
2. Installs a root-owned backend in `/usr/local/libexec`.
3. Writes the fixed keyboard profile to `/etc/keyd/alt-command.conf`.
4. Enables and starts `keyd.service`, then reloads the profile.

No logout is required. Try the shortcuts in a text editor. Closing the app window
does not turn remapping off.

## Scope, persistence, and permissions

The profile applies to **all keyboards matched by keyd, all applications, and all
sessions on the machine**. It is not limited to one user or to the external
Windows keyboard. It persists across reboot while enabled and may affect the
login screen or text consoles where keyd handles the device.

Every toggle uses polkit authentication. The app does not save your password,
add your user to an input-access group, or install passwordless remapping rules.
The privileged backend supports fixed setup/enable/disable operations.

Turning the toggle off removes this app's profile and reloads keyd. It leaves
keyd installed and its service enabled for possible other uses.

### Files installed by the Debian package

| Path | Purpose |
| --- | --- |
| `/usr/bin/kamalt-command` | Command-line launcher |
| `/usr/share/kamalt-command/` | App and backend status logic |
| `/usr/share/applications/io.github.altcommand.App.desktop` | System application launcher |
| `/usr/libexec/kamalt-command-backend` | Package-owned privileged backend |
| `/usr/share/doc/kamalt-command/README.md` | Installed documentation |
| `/etc/keyd/alt-command.conf` | Shared managed profile, created only when enabled |

APT owns and updates the packaged backend; the app does not replace it itself.

### Files installed from source

| Path | Purpose |
| --- | --- |
| `~/.local/share/alt-command/app.py` | GNOME interface |
| `~/.local/share/alt-command/backend.py` | Setup source and status logic |
| `~/.local/share/applications/io.github.altcommand.App.desktop` | Application launcher |
| `/usr/local/libexec/alt-command-backend` | Root-owned privileged backend |
| `/etc/keyd/alt-command.conf` | Enabled keyboard profile; removed when disabled |

The downloaded keyd package also installs its own executable and systemd unit.

### Existing remapping tools

The backend refuses to enable alongside other `/etc/keyd/*.conf` profiles because
competing device matches can prevent the intended mappings. It also refuses to
overwrite a modified kamalt-command profile. Known, exact prior versions of this
app's profile can be upgraded automatically.

If you already use keyd, integrate the mappings deliberately into your existing
setup. Other tools that grab keyboard devices, such as input-remapper, can also
conflict; check their configuration before enabling both.

## Updating a source installation

From your cloned repository:

```sh
git pull --ff-only
/usr/bin/python3 install-local.py
```

Close and reopen kamalt-command. If remapping is on, toggle it off and back on to
apply the update, completing the authentication prompts. If it is off, enable
it once. The app refreshes the root-owned backend when it detects a new version.

Cancelling authentication leaves the existing profile in place. If applying a
profile fails, the backend restores the previous profile and attempts to reload
it. The GUI restores the switch and reports the error.

## Troubleshooting

### The app does not open or reports `No module named gi`

Use `/usr/bin/python3` and install the GUI dependencies listed above. A Python
interpreter from pyenv or a virtual environment may not see system packages.

### Authentication is cancelled or no password dialog appears

Try the toggle again. Ensure polkit, `pkexec`, and the session's authentication
agent are installed and running. Administrator access is required.

### `keyd` executable is missing

Check both supported names:

```sh
command -v keyd.rvaiya
command -v keyd
```

Install the keyd package if neither is present. Current app versions recognize
Ubuntu's renamed executable; update the app if an older version looks only for
`/usr/bin/keyd`.

### The toggle fails, or shortcuts have no effect

Inspect the service, logs, and saved profile:

```sh
systemctl status keyd --no-pager
journalctl -u keyd -n 50 --no-pager
cat /etc/keyd/alt-command.conf
/usr/bin/python3 ~/.local/share/alt-command/backend.py status
```

If journal access is restricted, use `sudo journalctl`. A successful status reports
`installed`, `configured`, and `enabled` as `true`. Check that keyd's log matches
your keyboard to the profile. If the service stopped, toggle to restart it.

For an existing-profile error, inspect `/etc/keyd` and resolve competing profiles
without deleting configurations you want to keep. For an edited-profile error,
preserve your custom changes before restoring the app's managed profile.

### A shortcut works in one app but not another

The app emits keys; it does not implement application commands. Check the target
application's bindings, particularly terminal copy/paste, quit, redo, and editor
Home/End behavior. Also check the keyboard layout and other remapping tools.

### Emergency recovery

keyd's emergency sequence **Backspace+Escape+Enter** terminates the daemon.
You can also stop it from a terminal:

```sh
sudo systemctl stop keyd
```

An enabled service/profile can return on reboot. To disable this app's mappings
persistently, use the toggle or the installed backend:

```sh
# Debian package:
sudo /usr/bin/python3 /usr/libexec/kamalt-command-backend disable
# Source installation instead:
# sudo /usr/bin/python3 /usr/local/libexec/alt-command-backend disable
```

## Uninstalling a source installation

Turn remapping off first, then close the app. Alternatively, run the backend's
`disable` command above. Remove only the app's installed files:

```sh
rm -r ~/.local/share/alt-command
rm ~/.local/share/applications/io.github.altcommand.App.desktop
sudo rm /usr/local/libexec/alt-command-backend
```

If the backend is unavailable, remove the managed profile and reload keyd using
the executable installed on your system:

```sh
sudo rm /etc/keyd/alt-command.conf
sudo keyd.rvaiya reload   # Ubuntu/Debian executable name
# Or: sudo keyd reload   # Upstream executable name
```

keyd is left installed. Remove it separately with your package manager only if
nothing else uses it. Deleting the cloned repository alone does not uninstall
the app or disable remapping.

## Development and validation

Source layout:

- `app.py`: GTK/libadwaita interface and asynchronous privileged calls.
- `backend.py`: executable discovery, profile management, upgrades, and rollback.
- `install-local.py`: per-user launcher installation.
- `tests/test_backend.py`: backend tests with mocked system operations.
- `tests/*.t`: actual keyd input/output fixtures.
- `tests/run_keyd_tests.py`: builds an upstream test harness in a temporary directory.

Run the backend tests without installing keyd or accessing keyboard devices:

```sh
/usr/bin/python3 -m unittest discover -s tests -v
```

To run the keyboard fixtures, install a C compiler and Git, then:

```sh
git clone --depth 1 --branch v2.5.0 https://github.com/rvaiya/keyd.git .validation/keyd
/usr/bin/python3 tests/run_keyd_tests.py .validation/keyd
```

If the checkout already exists, reuse it instead of cloning again. GitHub Actions
runs the backend tests, Python compilation checks, and all keyboard fixtures
against keyd v2.5.0 commit `f33dca879a3f871ee2e0fa9c1efd6e8dabb21ed3`.

The suite currently contains **14 backend tests, 4 packaging tests, and 22 input/output fixtures**.
It covers remapping, modifier handling, unchanged Alt+Tab/AltGr, prior-profile
upgrades, executable discovery, rollback, package contents, and removal behavior. These checks do not
install a daemon or change keyboard input. The GUI and authentication cancellation
were also exercised locally; application-specific behavior needs manual checking
in the target applications.

## Building and publishing a Debian release

The builder requires Python 3, Git, and `dpkg-deb` (provided by `dpkg`). It does
not require root or install the resulting package:

```sh
/usr/bin/python3 scripts/build_deb.py
```

The output is `dist/kamalt-command_<version>_all.deb`. `VERSION` sets the package
version. Build timestamps use `SOURCE_DATE_EPOCH` when set, or the latest Git
commit timestamp. Generated packages and validation checkouts are ignored by Git.

Inspect or dry-run the local package:

```sh
dpkg-deb --info dist/kamalt-command_0.1.2_all.deb
dpkg-deb --contents dist/kamalt-command_0.1.2_all.deb
apt-get -s install ./dist/kamalt-command_0.1.2_all.deb
```

The `Debian release` GitHub Actions workflow runs for `v*` tags. It requires the
tag to match `VERSION`, runs backend/package and keyboard tests, validates the
desktop launcher, performs an isolated Ubuntu 26.04 APT install/remove check,
and publishes the `.deb` and `SHA256SUMS` as release assets.

For a future release, update `VERSION`, commit and push the change, then push the
matching version tag. Publishing requires repository write access. A checksum
helps detect download corruption; it is not a package signature.

With Docker available, you can repeat the isolated APT lifecycle check:

```sh
sh scripts/test_deb.sh dist/kamalt-command_0.1.2_all.deb
```

The container checks dependency installation and removal with no enabled profile.
It does not run a GNOME session or validate live keyd input inside the container.
