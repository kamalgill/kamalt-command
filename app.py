#!/usr/bin/python3
"""A single-switch GNOME frontend for the kamalt-command keyd profile."""
import json
from pathlib import Path
import subprocess
import threading
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, GLib, Gtk

import backend


class KamaltCommand(Adw.Application):
    def __init__(self):
        super().__init__(application_id='io.github.altcommand.App')
        self.connect('activate', self.activate)
        self.busy = False
        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', lambda *_args: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action('app.quit', ['<Control>q'])

    def activate(self, _app):
        if self.get_active_window():
            self.get_active_window().present()
            return
        self.window = Adw.ApplicationWindow(application=self, title='kamalt-command',
                                           default_width=460, default_height=660)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.append(Adw.HeaderBar())
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20,
                          margin_top=20, margin_bottom=28, margin_start=28, margin_end=28)
        icon = Gtk.Image.new_from_icon_name('input-keyboard-symbolic')
        icon.set_pixel_size(64)
        content.append(icon)
        title = Gtk.Label(label='Make Alt feel like Command')
        title.add_css_class('title-2')
        content.append(title)
        description = Gtk.Label(label='Mac-style editing shortcuts on your Windows keyboard.',
                                wrap=True, justify=Gtk.Justification.CENTER)
        description.add_css_class('dim-label')
        content.append(description)
        group = Adw.PreferencesGroup()
        self.row = Adw.ActionRow(title='kamalt-command', subtitle='Off · normal keyboard shortcuts')
        self.switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.switch.connect('state-set', self.toggle)
        self.row.add_suffix(self.switch)
        self.row.set_activatable_widget(self.switch)
        group.add(self.row)
        content.append(group)
        grid = Gtk.Grid(row_spacing=12, column_spacing=22, halign=Gtk.Align.CENTER)
        for index, (keys, action) in enumerate((('Alt + C', 'Copy'), ('Alt + V', 'Paste'),
                                               ('Alt + X', 'Cut'), ('Alt + A', 'Select all'),
                                               ('Alt + Z', 'Undo'), ('Alt + Shift + Z', 'Redo'),
                                               ('Alt + F', 'Find'), ('Alt + S', 'Save'),
                                               ('Alt + W', 'Close window'), ('Alt + Q', 'Quit app'),
                                               ('Alt + ←', 'Go to start of line'),
                                               ('Alt + →', 'Go to end of line'),
                                               ('Alt + ↑', 'Go to top of page'),
                                               ('Alt + ↓', 'Go to bottom of page'),
                                               ('Alt + Shift + →', 'Select to end of line'),
                                               ('Alt + Shift + ←', 'Select to start of line'))):
            key = Gtk.Label(label=keys, xalign=0)
            key.add_css_class('monospace')
            grid.attach(key, 0, index, 1, 1)
            grid.attach(Gtk.Label(label=action, xalign=0), 1, index, 1, 1)
        content.append(grid)
        self.note = Gtk.Label(wrap=True, justify=Gtk.Justification.CENTER)
        self.note.add_css_class('dim-label')
        content.append(self.note)
        clamp = Adw.Clamp(maximum_size=480)
        clamp.set_child(content)
        scroll = Gtk.ScrolledWindow(vexpand=True, hscrollbar_policy=Gtk.PolicyType.NEVER)
        scroll.set_child(clamp)
        box.append(scroll)
        self.window.set_content(box)
        self.refresh()
        self.window.present()

    def refresh(self):
        state = backend.status()
        self.switch.set_state(state['enabled'])
        self.switch.set_active(state['enabled'])
        self.row.set_subtitle('On · works even when this window is closed' if state['enabled'] else
                              'Service stopped · toggle to restart' if state['configured'] else
                              'Off · normal keyboard shortcuts')
        if state['enabled'] and not state['installed']:
            self.row.set_subtitle('On · update ready; toggle off/on to apply')
        self.note.set_label('Left Alt on all keyboards. Alt+Tab and right Alt keep working.\n'
                            'Terminal shortcuts may differ.' if state['installed'] else
                            'Toggle to set up or update the keyboard service.\nAdministrator authentication is required.')
        return state

    def toggle(self, _switch, enabled):
        if self.busy or enabled == self.switch.get_state():
            return True
        self.busy = True
        self.switch.set_sensitive(False)
        self.row.set_subtitle('Applying… complete the administrator prompt')
        state = backend.status()
        operation = 'enable' if enabled else 'disable'
        target = backend.INSTALLED
        if not state['installed']:
            operation = 'setup' if enabled else 'setup-disable'
            target = Path(__file__).with_name('backend.py')
        def work():
            try:
                result = subprocess.run(['/usr/bin/pkexec', '/usr/bin/python3', str(target), operation],
                                        capture_output=True, text=True)
                error = None if result.returncode == 0 else (
                    'Administrator authentication was cancelled.' if result.returncode in (126, 127) else
                    result.stderr.strip() or 'The keyboard service could not be updated.')
            except Exception as exception:
                error = str(exception)
            GLib.idle_add(self.finished, error)
        threading.Thread(target=work, daemon=True).start()
        return True

    def finished(self, error):
        self.refresh()
        self.busy = False
        self.switch.set_sensitive(True)
        if error:
            dialog = Adw.MessageDialog(transient_for=self.window, modal=True,
                                       heading='Could not change shortcuts', body=error)
            dialog.add_response('close', 'Close')
            dialog.set_default_response('close')
            dialog.present()
        return GLib.SOURCE_REMOVE


if __name__ == '__main__':
    KamaltCommand().run()
