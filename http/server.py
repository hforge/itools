# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from os import fstat
from sys import stdout

# Import from itools
from soup import SoupServer


class HTTPServer(SoupServer):

    def __init__(self, address=None, port=8080, access_log=None):
        SoupServer.__init__(self, address=address, port=port)

        # Keep arguments
        self.address = address
        self.port = port
        self.access_log = access_log

        # Open log files
        if access_log is not None:
            self.access_log_file = open(access_log, 'a+')


    def log_access(self, line):
        # Default: stdout
        if self.access_log is None:
            stdout.write(line)
            return

        # File
        log = self.access_log_file
        if fstat(log.fileno())[3] == 0:
            log = open(self.access_log, 'a+')
            self.access_log_file = log
        log.write(line)
        log.flush()


    def listen(self):
        SoupServer.start(self)
        address = self.address if self.address is not None else '*'
        print 'Listen %s:%d' % (address, self.port)


    def stop(self):
        SoupServer.stop(self)
        if self.access_log:
            self.access_log_file.close()
