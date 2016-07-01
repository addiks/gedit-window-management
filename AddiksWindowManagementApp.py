# Copyright (C) 2015 Gerrit Addiks <gerrit@addiks.net>
# https://github.com/addiks/gedit-window-management
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GObject, Gedit, PeasGtk, Gio
from addiks_window_management.gladehandler import GladeHandler
import os

class AddiksWindowManagementApp(GObject.Object, Gedit.AppActivatable, PeasGtk.Configurable):
    app = GObject.property(type=Gedit.App)

    def __init__(self):
        GObject.Object.__init__(self)
        self._glade_handler = None
        self._glade_builder = None
        self._settings = None

        if not os.path.exists(os.path.dirname(__file__)+"/gschemas.compiled"):
            pass

        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            os.path.dirname(__file__),
            Gio.SettingsSchemaSource.get_default(),
            False,
        )
        schema = schema_source.lookup('de.addiks.gedit.window_management', False)
        self._settings = Gio.Settings.new_full(schema, None, None)

        geditUIPreferences = Gio.Settings.new("org.gnome.gedit.preferences.ui")

    def do_activate(self):
        AddiksWindowManagementApp.__instance = self
        # gsettings set org.gnome.gedit.preferences.ui notebook-show-tabs-mode never

    def do_deactivate(self):
        AddiksWindowManagementApp.__instance = None
        # gsettings set org.gnome.gedit.preferences.ui notebook-show-tabs-mode auto

    ### SINGLETON

    __instance = None

    @staticmethod
    def get():
        if AddiksWindowManagementApp.__instance == None:
            AddiksWindowManagementApp.__instance = AddiksWindowManagementApp()
        return AddiksWindowManagementApp.__instance

    ### CONFIGURATION

    def do_create_configure_widget(self):
        filename = os.path.dirname(__file__)+"/window-management.glade"
        self._glade_builder = Gtk.Builder()
        self._glade_builder.add_objects_from_file(filename, ["gridConfig"])
        self._glade_handler = GladeHandler(self, self._glade_builder)
        self._glade_builder.connect_signals(self._glade_handler)
        for key, objectName in [
            ["autoresize",      "switchConfigAutoresize"],
            ["no-tabs",         "switchConfigNoTabs"],
            ["no-double-files", "switchConfigNoDoubleFiles"],
            ["hide-toolbar",    "switchConfigHideToolbar"]]:
            switch = self._glade_builder.get_object(objectName)
            self._settings.bind(key, switch, "active", Gio.SettingsBindFlags.DEFAULT)
        return self._glade_builder.get_object("gridConfig")

    def set_config(self, key, is_active):
        geditUIPreferences = Gio.Settings.new("org.gnome.gedit.preferences.ui")
        showTabsModeKey = "notebook-show-tabs-mode"
        if key == 'no-tabs' and showTabsModeKey in geditUIPreferences.list_keys():
            if is_active:
                mode = 0 # "never"
            else:
                mode = 1 # "auto"
            geditUIPreferences.set_enum(showTabsModeKey, mode)

    def get_settings(self):
        return self._settings

    ### WINDOW / VIEW MANAGEMENT

    windows = []

    def get_all_windows(self):
        return self.windows

    def register_window(self, window):
        if window not in self.windows:
            self.windows.append(window)

    def unregister_window(self, window):
        if window in self.windows:
            self.windows.remove(window)

    def get_window_by_view(self, view):
        for window in self.windows:
            if view in window.window.get_views():
                return window

    views = []

    def get_all_views(self):
        return self.views

    def register_view(self, view):
        if view not in self.views:
            self.views.append(view)

    def unregister_view(self, view):
        if view in self.views:
            self.views.remove(view)

