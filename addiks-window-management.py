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

from gi.repository import Gtk, GObject, Gedit, PeasGtk, Gio, Pango, GLib
from _thread import start_new_thread
from addiks_window_management.helpers import *
from addiks_window_management.gladehandler import GladeHandler
import os
from time import sleep

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
            ["no-double-files", "switchConfigNoDoubleFiles"]]:
            switch = self._glade_builder.get_object(objectName)
            self._settings.bind(key, switch, "active", Gio.SettingsBindFlags.DEFAULT)
        return self._glade_builder.get_object("gridConfig")

    def set_config(self, key, is_active):
        if key == 'no-tabs':
            if is_active:
                mode = 0 # "never"
            else:
                mode = 1 # "auto"
            geditUIPreferences = Gio.Settings.new("org.gnome.gedit.preferences.ui")
            geditUIPreferences.set_enum("notebook-show-tabs-mode", mode)

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

class AddiksWindowManagementWindow(GObject.Object, Gedit.WindowActivatable):
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        AddiksWindowManagementApp.get().register_window(self)
        plugin_path = os.path.dirname(__file__)
        
        self._actions = Gtk.ActionGroup("AddiksAutoresizeMenuActions")
        self._actions.add_actions([("FitWindowToContentAction", Gtk.STOCK_INFO, "Fit window", "<Ctrl><Alt>P", "", self.fit_window),])

        self._ui_manager = self.window.get_ui_manager()
        self._ui_manager.insert_action_group(self._actions)
        self._ui_manager.add_ui_from_string(file_get_contents(plugin_path + "/menubar.xml"))
        self._ui_manager.ensure_update()

        self.window.connect("tab-added", self.on_tab_added)

    def do_deactivate(self):
        AddiksWindowManagementApp.get().unregister_window(self)
        
    def do_update_state(self):
        document = self.window.get_active_document()
        textView = self.window.get_active_view()
        if textView != None:
            if "addiks_autoresize_event_registered" not in dir(textView):
                textView.addiks_autoresize_event_registered = True
                textView.connect("key-release-event", self.on_auto_fit_window)
            self.on_auto_fit_window()

    def on_tab_added(self, window, tab, userData=None):
        event = Gtk.get_current_event()
        time  = Gtk.get_current_event_time()

        if AddiksWindowManagementApp.get().get_settings().get_boolean("no-double-files"):
            view = tab.get_view()
            document = view.get_buffer()
            myLocation = document.get_location()
            if myLocation != None:
                myPath = myLocation.get_path()
                for otherWindow in AddiksWindowManagementApp.get().get_all_windows():
                    for otherView in otherWindow.window.get_views():
                        otherDocument = otherView.get_buffer()
                        otherLocation = otherDocument.get_location()
                        if otherLocation != None:
                            path = otherLocation.get_path()
                            if path == myPath and otherWindow.window != window:
                                myTab = window.get_tab_from_location(myLocation)
                                otherTab = otherWindow.window.get_tab_from_location(otherLocation)
                                start_new_thread(self.delayed_close_tab, (otherWindow.window, otherTab, ))
                                start_new_thread(self.delayed_present, (window, ))

        if len(self.window.get_views())>1 and AddiksWindowManagementApp.get().get_settings().get_boolean("no-tabs"):
            view = tab.get_view()

            ### DETERMINE LOCATION/LINE/COLUMN

            document = view.get_buffer()
            location = document.get_location()

            insertMark = view.get_buffer().get_insert()
            insertIter = view.get_buffer().get_iter_at_mark(insertMark)

            line   = insertIter.get_line()
            column = insertIter.get_line_offset()

            ### CLOSE CURRENT TAB

            GLib.idle_add(self.delayed_close_tab, window, tab)
            
            ### OPEN NEW TAB IN NEW WINDOW

            newWindow = AddiksWindowManagementApp.get().app.create_window()

            if location != None:
                tab = newWindow.create_tab_from_location(location, None, line, column, False, True)
                
                document = tab.get_view().get_buffer()
                textIter = document.get_end_iter().copy()
                textIter.set_line(line)
                textIter.set_line_offset(column)
                tab.get_view().scroll_to_iter(textIter, 0.3, False, 0.0, 0.5)

            else:
                tab = newWindow.create_tab(True)
            
            start_new_thread(self.delayed_present, (newWindow, ))

    def delayed_present(self, window):
        sleep(0.02)
        GLib.idle_add(window.present)

    def delayed_close_tab(self, window, tab):
        sleep(0.01)
        window.close_tab(tab)
        if len(window.get_views())<=0:
            window.close()

    def on_auto_fit_window(self, action=None, data=None):
        if AddiksWindowManagementApp.get().get_settings().get_boolean("autoresize"):
            self.fit_window(action, data)

    def fit_window(self, action=None, data=None):
        document = self.window.get_active_document()
        textView = self.window.get_active_view()

        if document != None:
            bounds = document.get_bounds()
            content = document.get_text(bounds[0], bounds[1], True)

            lines = content.split("\n")
            height = len(lines)
            width = 0
            for line in lines:
                if width < len(line):
                    width = len(line)

            height += 3 # three extra lines for status-bar
            width  += 3 # three extra columns for line-numbers

            style = textView.get_style()
            font = style.font_desc
            fontSize = font.get_size() / Pango.SCALE

            # TODO: get actual character sizes
            height *= (17 * (fontSize / 11.0))
            width  *= (8  * (fontSize / 11.0))

            # TODO: make bounds configurable
            if height > 800:
                height = 800
            if width > 1400:
                width = 1400

            if width < 200:
                width = 200
            if height < 50:
                height = 50

            self.window.resize(width, height)

    #        rect = textView.get_allocation()
    #        print((rect.width))
        
class AddiksWindowManagementView(GObject.Object, Gedit.ViewActivatable):
    view = GObject.property(type=Gedit.View)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        pass

    def do_deactivate(self):
        AddiksWindowManagementApp.get().unregister_view(self)

