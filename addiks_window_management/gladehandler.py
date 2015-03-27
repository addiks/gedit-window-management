# Copyright (C) 2015 Gerrit Addiks <gerrit@addiks.net>
# https://github.com/addiks/gedit-dbgp-plugin
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

from gi.repository import GLib, Gtk, Gdk
from helpers import *
from os.path import expanduser
import traceback

class GladeHandler:

    def __init__(self, plugin, builder):
        self._plugin  = plugin
        self._builder = builder

    ### CONFIGURATION

    def onConfigAutoresizeActivate(self, switch, userData=None):
        builder = self._builder
        switch = builder.get_object("switchConfigAutoresize")
        active = switch.get_active()
        self._plugin.set_config("autoresize", active)

    def onConfigNoTabsActivate(self, switch, userData=None):
        builder = self._builder
        switch = builder.get_object("switchConfigNoTabs")
        active = switch.get_active()
        self._plugin.set_config("no-tabs", active)

    def onConfigNoDoubleFilesActivate(self, switch, userData=None):
        builder = self._builder
        switch = builder.get_object("switchConfigNoDoubleFiles")
        active = switch.get_active()
        self._plugin.set_config("no-double-files", active)

