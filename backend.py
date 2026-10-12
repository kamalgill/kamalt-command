#!/usr/bin/python3
"""Fixed-operation privileged backend; no arbitrary paths or commands accepted."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

CONFIG_DIR = Path('/etc/keyd')
CONFIG = CONFIG_DIR / 'alt-command.conf'
PACKAGED = Path(__file__).resolve() in (
    Path('/usr/share/kamalt-command/backend.py'),
    Path('/usr/libexec/kamalt-command-backend'),
)
INSTALLED = Path('/usr/libexec/kamalt-command-backend') if PACKAGED else Path('/usr/local/libexec/alt-command-backend')
PROFILE = '''# Managed by Alt Command
[ids]
*

[main]
leftalt = layer(command)

[command:A]
c = C-c
v = C-v
x = C-x
a = C-a
z = C-z
f = C-f
s = C-s
w = A-f4
q = C-q
left = home
right = end

[shift]

[command+shift]
right = S-end
left = S-home
z = C-S-z
'''
# Exact previous app profiles; accept them for upgrades, but preserve custom edits.
PREVIOUS_PROFILE = PROFILE.replace('left = home\nright = end\n', '')
EDITING_PROFILE = PREVIOUS_PROFILE.replace('w = A-f4\nq = C-q\n', '')
LEGACY_PROFILES = (PREVIOUS_PROFILE, EDITING_PROFILE,
                  EDITING_PROFILE.replace('x = C-x\na = C-a\nz = C-z\nf = C-f\ns = C-s\n', '')
                  .replace('z = C-S-z\n', ''))


def keyd_binary():
    # Debian/Ubuntu rename this executable to avoid a package-name collision.
    # Use only administrator-owned executable directories, even for status calls.
    for name in ('keyd.rvaiya', 'keyd'):
        executable = shutil.which(name, path='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')
        if executable:
            return executable
    return None


def require_keyd():
    executable = keyd_binary()
    if executable is None:
        raise RuntimeError('The keyd executable was not found. Install the keyd package and try again.')
    return executable


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or
                           f'{args[0]} failed ({result.returncode})')
    return result.stdout.strip()


def active():
    return subprocess.run(['/usr/bin/systemctl', 'is-active', '--quiet', 'keyd'],
                          capture_output=True, timeout=10).returncode == 0


def status():
    configured = CONFIG.is_file() and CONFIG.read_text() in (PROFILE, *LEGACY_PROFILES)
    return {'installed': (INSTALLED.is_file() and keyd_binary() is not None and
                          INSTALLED.read_text() == Path(__file__).read_text()),
            'configured': configured, 'enabled': configured and active()}


def atomic_write(path, data):
    fd, temporary = tempfile.mkstemp(prefix='.alt-command-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def set_enabled(enabled):
    executable = require_keyd()
    CONFIG_DIR.mkdir(mode=0o755, exist_ok=True)
    if CONFIG.is_symlink() or (CONFIG.exists() and CONFIG.read_text() not in (PROFILE, *LEGACY_PROFILES)):
        raise RuntimeError('The Alt Command config has been modified. Resolve it in /etc/keyd before toggling.')
    if enabled:
        others = list(CONFIG_DIR.glob('*.conf'))
        others = [p.name for p in others if p != CONFIG]
        if others:
            raise RuntimeError('Existing keyd profiles may conflict: ' + ', '.join(others) +
                               '. Integrate them before enabling Alt Command.')
    previous = CONFIG.read_text() if CONFIG.exists() else None
    try:
        if enabled:
            atomic_write(CONFIG, PROFILE)
            run('/usr/bin/systemctl', 'enable', '--now', 'keyd')
        else:
            CONFIG.unlink(missing_ok=True)
        if active():
            run(executable, 'reload')
        if enabled and not active():
            raise RuntimeError('The keyboard service did not start.')
    except Exception:
        if previous is None:
            CONFIG.unlink(missing_ok=True)
        else:
            atomic_write(CONFIG, previous)
        if active():
            run(executable, 'reload')
        raise


def setup(enabled=True):
    if PACKAGED:
        raise RuntimeError('This installation is managed by APT. Reinstall or update the kamalt-command package.')
    if keyd_binary() is None:
        if not Path('/usr/bin/apt-get').exists():
            raise RuntimeError('Install keyd using your distribution package manager first.')
        run('/usr/bin/apt-get', 'install', '-y', 'keyd')
    require_keyd()
    INSTALLED.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    # Install a root-owned copy so subsequent privileged calls never execute user-writable code.
    atomic_write(INSTALLED, Path(__file__).read_text())
    os.chmod(INSTALLED, 0o755)
    set_enabled(enabled)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('status', 'setup', 'setup-disable', 'enable', 'disable'):
        raise RuntimeError('Expected status, setup, setup-disable, enable, or disable.')
    operation = sys.argv[1]
    if operation == 'status':
        print(json.dumps(status()))
        return
    if os.geteuid() != 0:
        raise RuntimeError('Administrator authentication is required.')
    os.environ['PATH'] = '/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/bin'
    with open('/run/alt-command.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if operation in ('setup', 'setup-disable'):
            setup(operation == 'setup')
        else:
            set_enabled(operation == 'enable')
    print(json.dumps(status()))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
