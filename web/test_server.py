#!/usr/bin/env python2.4
# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import datetime
import sys

# Import from itools
from itools.resources import get_resource
from itools.handlers.Folder import Folder
from server import Server


class Time(Folder):

    def GET(self):
        now = datetime.datetime.now()
        return now.strftime('%Y %m %d %H:%M:%S')


class Static(Folder):
    pass



if __name__ == '__main__':
    args = sys.argv
    if len(args) == 2:
        arg = args[1]
        if arg == 'time':
            # The root of our data
            root = Time()

            # Build and start the server
            server = Server(root)
            server.start()

    print 'usage: python test_server.py time'
