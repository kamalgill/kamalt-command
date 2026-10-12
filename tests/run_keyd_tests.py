#!/usr/bin/python3
"""Run real input/output fixtures using an existing keyd v2.5.0 source checkout."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import backend


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 tests/run_keyd_tests.py /path/to/keyd-source')
    source = Path(sys.argv[1]).resolve()
    files = ['t/test-io.c', 'src/keyboard.c', 'src/string.c', 'src/macro.c',
             'src/config.c', 'src/log.c', 'src/ini.c', 'src/keys.c', 'src/unicode.c']
    with tempfile.TemporaryDirectory(prefix='alt-command-tests-') as directory:
        binary = Path(directory) / 'test-io'
        config = Path(directory) / 'profile.conf'
        config.write_text(backend.PROFILE)
        subprocess.run(['cc', '-DDATA_DIR=', '-o', str(binary),
                        *(str(source / name) for name in files)], check=True)
        subprocess.run([str(binary), str(config),
                        *(str(path) for path in sorted((ROOT / 'tests').glob('*.t')))], check=True)


if __name__ == '__main__':
    main()
