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
from time import strftime
from datetime import timedelta

# Import from itools
from soup import SoupServer
from itools.log import Logger, register_logger, log_info


class HTTPServer(SoupServer):

    def __init__(self, access_log=None):
        SoupServer.__init__(self)

        # The logger
        logger = AccessLogger(log_file=access_log)
        logger.launch_rotate(timedelta(weeks=3))
        register_logger(logger, 'itools.web_access')


    def log_access(self, host, request_line, status_code, body_length):
        now = strftime('%d/%b/%Y:%H:%M:%S')
        message = '%s - - [%s] "%s" %d %d\n' % (host, now, request_line,
                                                status_code, body_length)
        log_info(message, domain='itools.web_access')


    def listen(self, address, port):
        SoupServer.listen(self, address, port)
        address = address if address is not None else '*'
        print 'Listen %s:%d' % (address, port)


    def stop(self):
        SoupServer.stop(self)
        if self.access_log:
            self.access_log_file.close()



class AccessLogger(Logger):
    def format(self, domain, level, message):
        return message

