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

from gi.repository import Gtk, GObject, Gedit, Pango, GLib
from AddiksWindowManagementApp import AddiksWindowManagementApp
from _thread import start_new_thread
from addiks_window_management.helpers import *
from addiks_window_management.gladehandler import GladeHandler
import os
from time import sleep

class AddiksWindowManagementWindow(GObject.Object, Gedit.WindowActivatable):
    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        AddiksWindowManagementApp.get().register_window(self)
        plugin_path = os.path.dirname(__file__)

        if "get_ui_manager" in dir(self.window):# build menu for gedit 3.10 (global menu per window)
            self._ui_manager = self.window.get_ui_manager()

            self._actions = Gtk.ActionGroup("AddiksAutoresizeMenuActions")
            self._actions.add_actions([
                ("FitWindowToContentAction", Gtk.STOCK_INFO, "Fit window", "<Ctrl><Alt>P", "", self.fit_window),
            ])

            self._ui_manager.insert_action_group(self._actions)
            self._ui_manager.add_ui_from_string(file_get_contents(plugin_path + "/menubar.xml"))
            self._ui_manager.ensure_update()

        self.window.connect("tab-added", self.on_tab_added)

        if AddiksWindowManagementApp.get().get_settings().get_boolean("hide-toolbar"):
            self.set_toolbar_visible(False)

    def set_toolbar_visible(self, isVisible):
        windowChildren = self.window.get_children()
        box = windowChildren[0]
        paned = None
        for boxChild in box.get_children():
            if type(boxChild) == Gtk.Paned:
                paned = boxChild

        if paned != None:
            paned.set_visible(isVisible)

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
        wasClosed = False
        noTabsEnabled = AddiksWindowManagementApp.get().get_settings().get_boolean("no-tabs")

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
                                start_new_thread(self.delayed_close_tab, (window, tab))
                                start_new_thread(self.delayed_present, (otherWindow.window, ))
                                wasClosed = True

        if len(self.window.get_views())>1 and noTabsEnabled and not wasClosed:
            view = tab.get_view()

            ### DETERMINE LOCATION/LINE/COLUMN

            document = view.get_buffer()
            location = document.get_location()

            insertMark = view.get_buffer().get_insert()
            insertIter = view.get_buffer().get_iter_at_mark(insertMark)

            line   = insertIter.get_line()
            column = insertIter.get_line_offset()

            GLib.idle_add(self.delayed_close_tab, window, tab, True)

    def delayed_close_tab(self, window, tab, reOpen=False):
        location = None
        line = None
        column = None

        if reOpen:
            view = tab.get_view()
            document = view.get_buffer()
            location = document.get_location()

            insertMark = view.get_buffer().get_insert()
            insertIter = view.get_buffer().get_iter_at_mark(insertMark)

            line   = insertIter.get_line()
            column = insertIter.get_line_offset()

        GLib.idle_add(self.do_delayed_close_tab, window, tab, location, line, column)

    def do_delayed_close_tab(self, window, tab, location=None, line=None, column=None):
        window.close_tab(tab)
        if len(window.get_views())<=0:
            window.close()

        ### REOPEN IN NEW WINDOW
        if location != None:
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

            start_new_thread(self.delayed_present, (newWindow, line, column))

    def delayed_present(self, window, line=None, column=None):
        sleep(0.02)
        GLib.idle_add(self.__present, window, line, column)

    def __present(self, window, line=None, column=None):
        window.present()
        if line != None:
            if column == None:
                column = 0

#            print([line, column])

            textView = window.get_active_view()

            document = textView.get_buffer()
            textIter = document.get_end_iter().copy()
            textIter.set_line(line)
            textIter.set_line_offset(column)
            textView.scroll_to_iter(textIter, 0.3, False, 0.0, 0.5)

    def on_auto_fit_window(self, action=None, data=None):
        if AddiksWindowManagementApp.get().get_settings().get_boolean("autoresize"):
            self.fit_window(action, data)

    def fit_window(self, action=None, data=None):
        document = self.window.get_active_document()
        textView = self.window.get_active_view()
        scrolledWindow = textView.get_parent()
#        print(scrolledWindow)
#        print([
#            scrolledWindow.get_property("min-content-height"),
#            scrolledWindow.get_property("min-content-width"),
#        ])

        if document != None:
            bounds = document.get_bounds()
            content = document.get_text(bounds[0], bounds[1], True)

            lines = content.split("\n")
            height = len(lines)
            width = 0
            for line in lines:
                if width < len(line):
                    width = len(line)

            height += 1 # extra lines for status-bar
            width  += 5 # extra columns for line-numbers

            style = textView.get_style()
            font = style.font_desc
            fontSize = font.get_size() / Pango.SCALE

            # TODO: get actual character sizes
            height *= (17 * (fontSize / 11.0))
            width  *= (9  * (fontSize / 11.0))

            # TODO: make bounds configurable
            if height > 800:
                height = 800
            if width > 1400:
                width = 1400

            if width < 200:
                width = 200
            if height < 50:
                height = 50

            if False and type(scrolledWindow) == Gtk.ScrolledWindow:
                scrolledWindow.set_min_content_width(width)
                scrolledWindow.set_min_content_height(height)

            else:
                self.window.resize(width, height)
#                self.window.event("check-resize")

    #        rect = textView.get_allocation()
    #        print((rect.width))
