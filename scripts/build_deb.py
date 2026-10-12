#!/usr/bin/python3
"""Build an architecture-independent Debian package without root privileges."""
import gzip
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must contain a numeric major.minor.patch version.')
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    package = output / f'kamalt-command_{version}_all.deb'
    epoch = int(os.environ.get('SOURCE_DATE_EPOCH') or subprocess.check_output(
        ['git', 'log', '-1', '--format=%ct'], cwd=ROOT, text=True).strip())
    with tempfile.TemporaryDirectory(prefix='kamalt-command-deb-') as temporary:
        stage = Path(temporary)
        def write(relative, data, mode=0o644):
            path = stage / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
            path.chmod(mode)
        write('DEBIAN/control', f'''Package: kamalt-command
Version: {version}
Section: utils
Priority: optional
Architecture: all
Maintainer: Kamal Gill <133923+kamalgill@users.noreply.github.com>
Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1 (>= 1.2), pkexec, polkitd, systemd, keyd (>= 2.5.0)
Homepage: https://github.com/kamalgill/kamalt-command
Description: GNOME toggle for Mac-style Alt keyboard shortcuts
 Remap left Alt editing and navigation shortcuts with keyd on Linux.
 Provides a GTK 4 interface and an authenticated fixed-operation backend.
''')
        write('DEBIAN/prerm', (ROOT / 'packaging/prerm').read_text(), 0o755)
        for name in ('app.py', 'backend.py'):
            write(f'usr/share/kamalt-command/{name}', (ROOT / name).read_text())
        write('usr/libexec/kamalt-command-backend', (ROOT / 'backend.py').read_text(), 0o755)
        write('usr/bin/kamalt-command', '#!/bin/sh\nexec /usr/bin/python3 /usr/share/kamalt-command/app.py "$@"\n', 0o755)
        write('usr/share/applications/io.github.altcommand.App.desktop',
              (ROOT / 'packaging/kamalt-command.desktop').read_text())
        write('usr/share/doc/kamalt-command/README.md', (ROOT / 'README.md').read_text())
        changelog = stage / 'usr/share/doc/kamalt-command/changelog.gz'
        changelog.write_bytes(gzip.compress(
            f'kamalt-command ({version}) unstable; urgency=medium\n\n  * Initial Debian package.\n'.encode(), mtime=0))
        sums = ''.join(f'{hashlib.md5(path.read_bytes()).hexdigest()}  {path.relative_to(stage)}\n'
                       for path in sorted((stage / 'usr').rglob('*')) if path.is_file())
        write('DEBIAN/md5sums', sums)
        for path in stage.rglob('*'):
            os.utime(path, (epoch, epoch))
        os.utime(stage, (epoch, epoch))
        subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(package)],
                       check=True, env={**os.environ, 'SOURCE_DATE_EPOCH': str(epoch)})
    shutil.copyfile(ROOT / 'VERSION', output / 'VERSION')
    (output / 'RELEASE_NOTES.md').write_text(f'''Download `{package.name}` and install on a compatible Ubuntu/Debian GNOME system:

```sh
sudo apt install ./{package.name}
kamalt-command
```

APT installs keyd and the GUI dependencies from your configured repositories.
Remapping is not automatically enabled; turn on the app toggle and complete the administrator prompt.
The package is architecture-independent (`all`); dependencies must be available for your system.

See the [README](https://github.com/kamalgill/kamalt-command#readme) for all mappings, requirements,
source-install migration, recovery, and removal instructions. SHA256SUMS contains the package checksum.

Packaging is validated by archive extraction, backend tests, and simulated removal/upgrade checks.
Live apt installation and desktop behavior are not certified on every Ubuntu/Debian version.
''')
    return package


if __name__ == '__main__':
    print(build())
