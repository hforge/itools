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
from sys import stdout
from time import strftime
from traceback import format_exc

# Import from itools
from itools.log import log_error


class Log(object):

    def __init__(self, access_log=None):
        self.access_log = access_log
        if access_log is not None:
            self.access_log_file = open(access_log, 'a+')


    def format_access(self, conn, request, response):
        # Common Log Format
        #  - IP address of the client
        #  - RFC 1413 identity (not available)
        #  - username (XXX not provided right now, should we?)
        #  - time (XXX we use the timezone name, while we should use the
        #    offset, e.g. +0100)
        #  - the request line
        #  - the status code
        #  - content length of the response
        host = request.get_remote_ip()
        if host is None:
            host, port = conn.getpeername()
        ts = strftime('%d/%b/%Y:%H:%M:%S %Z')
        request_line = request.request_line
        status = response.status
        length = response.get_content_length()
        line = '{0} - - [{1}] "{2}" {3} {4}\n'
        return line.format(host, ts, request_line, status, length)


    def log_access(self, conn, request, response):
        line = self.format_access(conn, request, response)

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


    def log_error(self):
        error = format_exc()
        log_error(error)

