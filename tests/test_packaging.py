import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import backend


class PackagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('build_deb', ROOT / 'scripts/build_deb.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        cls.package = builder.build()
        cls.temporary = tempfile.TemporaryDirectory()
        cls.extracted = Path(cls.temporary.name)
        subprocess.run(['dpkg-deb', '--raw-extract', str(cls.package), str(cls.extracted)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_metadata_and_system_installation(self):
        control = (self.extracted / 'DEBIAN/control').read_text()
        self.assertIn('Architecture: all', control)
        self.assertIn('keyd (>= 2.5.0)', control)
        self.assertEqual((self.extracted / 'usr/libexec/kamalt-command-backend').read_text(),
                         (ROOT / 'backend.py').read_text())
        for name in ('usr/bin/kamalt-command', 'usr/libexec/kamalt-command-backend', 'DEBIAN/prerm'):
            self.assertTrue((self.extracted / name).stat().st_mode & 0o111)
        self.assertFalse((self.extracted / 'etc/keyd/kamalt-command.conf').exists())
        self.assertFalse((self.extracted / 'DEBIAN/postinst').exists())
        launchers = self.extracted / 'usr/share/applications'
        self.assertEqual([p.name for p in launchers.iterdir()], ['io.github.kamaltcommand.App.desktop'])
        self.assertIn("application_id='io.github.kamaltcommand.App'",
                      (self.extracted / 'usr/share/kamalt-command/app.py').read_text())

    def test_removal_disables_but_upgrade_preserves_profile(self):
        self.check_removal_script('remove', expected_calls='disable\n')
        self.check_removal_script('upgrade', expected_calls='')

    def test_failed_disable_blocks_removal(self):
        self.check_removal_script('remove', expected_calls='disable\n', failure=True)

    def test_packaged_backend_uses_package_owned_path(self):
        for location in ('/usr/share/kamalt-command/backend.py', '/usr/libexec/kamalt-command-backend'):
            namespace = {'__file__': location, '__name__': 'packaged_backend_test'}
            exec(compile((ROOT / 'backend.py').read_text(), location, 'exec'), namespace)
            self.assertTrue(namespace['PACKAGED'])
            self.assertEqual(namespace['INSTALLED'], Path('/usr/libexec/kamalt-command-backend'))
            with self.assertRaisesRegex(RuntimeError, 'managed by APT'):
                namespace['setup']()

    def check_removal_script(self, operation, expected_calls, failure=False):
        # Execute the shipped script against isolated paths and a fake backend;
        # never touch host keyboard configuration or services during testing.
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            config = folder / 'profile.conf'
            config.write_text(backend.PROFILE)
            calls = folder / 'calls'
            fake = folder / 'backend.py'
            fake.write_text('from pathlib import Path\nimport sys\n'
                            f'Path({str(calls)!r}).write_text(sys.argv[1] + "\\n")\n'
                            f'sys.exit({1 if failure else 0})\n')
            script = (self.extracted / 'DEBIAN/prerm').read_text().replace(
                '/etc/keyd/kamalt-command.conf', str(config)).replace(
                '/usr/libexec/kamalt-command-backend', str(fake))
            result = subprocess.run(['/bin/sh', '-s', '--', operation], input=script,
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 1 if failure else 0)
            self.assertEqual(calls.read_text() if calls.exists() else '', expected_calls)


class SourceInstallTests(unittest.TestCase):
    def test_source_installer_uses_current_paths_and_launcher(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(ROOT / 'install-local.py')],
                           env={**os.environ, 'HOME': directory}, check=True, capture_output=True)
            share = Path(directory) / '.local/share'
            self.assertEqual(sorted(p.name for p in share.iterdir()), ['applications', 'kamalt-command'])
            launchers = list((share / 'applications').iterdir())
            self.assertEqual([p.name for p in launchers], ['io.github.kamaltcommand.App.desktop'])
            self.assertIn(str(share / 'kamalt-command/app.py'), launchers[0].read_text())


if __name__ == '__main__':
    unittest.main()
