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

import os

def file_get_contents(filename):
    """ retrieves the contents of a file. """
    with open(filename, encoding = "ISO-8859-1") as f:
        return f.read()

def group(lst, n):
    """group([0,3,4,10,2,3], 2) => [(0,3), (4,10), (2,3)]
    
    Group a list into consecutive n-tuples. Incomplete tuples are
    discarded e.g.
    
    >>> group(range(10), 3)
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]

    SOURCE: http://code.activestate.com/recipes/303060-group-a-list-into-sequential-n-tuples/

    """
    return zip(*[lst[i::n] for i in range(n)])

def intersect(a, b):
    return list(set(a) & set(b))

def get_namespace_by_classname(className):
    namespace = "\\"
    newClassName = className
    
    if className != None and className.find("\\") >= 0:
        classNameParts = className.split("\\")
        newClassName   = classNameParts.pop()
        namespace      = "\\".join(classNameParts)
        if len(namespace)<=0:
            namespace = "\\"

    return (namespace, newClassName)

def debug(message):
    with open("/tmp/ga_debug.log", "a+") as f:
        f.write(str(message) + "\n")
 
