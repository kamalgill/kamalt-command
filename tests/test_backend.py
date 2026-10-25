import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import backend


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.config = self.directory / 'kamalt-command.conf'
        self.patches = [patch.object(backend, 'CONFIG_DIR', self.directory),
                        patch.object(backend, 'CONFIG', self.config),
                        patch.object(backend, 'active', return_value=True),
                        patch.object(backend, 'run'),
                        patch.object(backend.shutil, 'which', return_value='/usr/bin/keyd.rvaiya')]
        self.mocks = [p.start() for p in self.patches]

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_enable_disable_roundtrip(self):
        backend.set_enabled(True)
        self.assertEqual(self.config.read_text(), backend.PROFILE)
        self.assertTrue(backend.status()['enabled'])
        backend.set_enabled(False)
        self.assertFalse(self.config.exists())
        self.assertFalse(backend.status()['enabled'])

    def test_other_profiles_are_not_overwritten(self):
        other = self.directory / 'custom.conf'
        other.write_text('[ids]\n*\n')
        with self.assertRaisesRegex(RuntimeError, 'Existing keyd profiles'):
            backend.set_enabled(True)
        self.assertEqual(other.read_text(), '[ids]\n*\n')
        self.assertFalse(self.config.exists())

    def test_modified_profile_is_preserved(self):
        self.config.write_text('custom')
        with self.assertRaisesRegex(RuntimeError, 'modified'):
            backend.set_enabled(False)
        self.assertEqual(self.config.read_text(), 'custom')

    def test_symlink_is_rejected(self):
        other = self.directory / 'other'
        other.write_text(backend.PROFILE)
        self.config.symlink_to(other)
        with self.assertRaisesRegex(RuntimeError, 'modified'):
            backend.set_enabled(True)
        self.assertEqual(other.read_text(), backend.PROFILE)

    def test_failed_enable_removes_new_profile(self):
        self.mocks[3].side_effect = [RuntimeError('start failed'), None]
        with self.assertRaisesRegex(RuntimeError, 'start failed'):
            backend.set_enabled(True)
        self.assertFalse(self.config.exists())

    def test_failed_disable_restores_profile(self):
        self.config.write_text(backend.PROFILE)
        self.mocks[3].side_effect = [RuntimeError('reload failed'), None]
        with self.assertRaisesRegex(RuntimeError, 'reload failed'):
            backend.set_enabled(False)
        self.assertEqual(self.config.read_text(), backend.PROFILE)

    def test_service_stopped_is_not_enabled(self):
        self.config.write_text(backend.PROFILE)
        self.mocks[2].return_value = False
        state = backend.status()
        self.assertTrue(state['configured'])
        self.assertFalse(state['enabled'])

    def test_ubuntu_renamed_executable_is_used_for_reload(self):
        with patch.object(backend.shutil, 'which', side_effect=lambda name, **kwargs:
                          '/usr/bin/keyd.rvaiya' if name == 'keyd.rvaiya' else None):
            backend.set_enabled(True)
        self.mocks[3].assert_any_call('/usr/bin/keyd.rvaiya', 'reload')

    def test_upstream_executable_is_supported(self):
        with patch.object(backend.shutil, 'which', side_effect=lambda name, **kwargs:
                          '/usr/local/bin/keyd' if name == 'keyd' else None):
            self.assertEqual(backend.keyd_binary(), '/usr/local/bin/keyd')

    def test_missing_executable_does_not_write_profile(self):
        with patch.object(backend.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(RuntimeError, 'executable was not found'):
                backend.set_enabled(True)
        self.assertFalse(self.config.exists())

    def test_old_installed_backend_requires_setup(self):
        installed = self.directory / 'backend'
        installed.write_text('old backend')
        with patch.object(backend, 'INSTALLED', installed):
            self.assertFalse(backend.status()['installed'])
            installed.write_text(Path(backend.__file__).read_text())
            self.assertTrue(backend.status()['installed'])

    def test_setup_disable_preserves_requested_off_state(self):
        with patch.object(backend, 'set_enabled') as set_enabled, \
                patch.object(backend, 'atomic_write'), \
                patch.object(backend.os, 'chmod'), \
                patch.object(backend, 'INSTALLED', self.directory / 'backend'):
            backend.setup(False)
        set_enabled.assert_called_once_with(False)


if __name__ == '__main__':
    unittest.main()
