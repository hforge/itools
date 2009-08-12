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
from signal import signal, SIGINT
from sys import stdout
from traceback import format_exc

# Import from pygobject
from gobject import MainLoop

# Import from itools
from itools.log import log_error
from app import Application
from app import MOVED, REDIRECT, UNAUTHORIZED, FORBIDDEN, NOT_FOUND, GONE
from exceptions import HTTPError
from context import HTTPContext
from soup import SoupServer


# When the number of connections hits the maximum number of connections
# allowed, new connections will be automatically responded with the
# "503 Service Unavailable" error
MAX_CONNECTIONS = 50


class HTTPServer(SoupServer):

    # The default application says "hello"
    app = Application()
    context_class = HTTPContext


    def __init__(self, address='', port=8080, access_log=None):
        SoupServer.__init__(self, address=address, port=port)

        # The server listens to...
        self.address = address
        self.port = port

        # Main Loop
        self.main_loop = MainLoop()

        # Logging
        self.access_log = access_log
        if access_log is not None:
            self.access_log_file = open(access_log, 'a+')


    #######################################################################
    # Logging
    #######################################################################
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


    def log_error(self):
        error = format_exc()
        log_error(error)


    #######################################################################
    # Start & Stop
    #######################################################################
    def start(self):
        signal(SIGINT, self.stop_gracefully)
        SoupServer.start(self)
        print 'Listen %s:%d' % (self.address, self.port)
        self.main_loop.run()


    def stop_gracefully(self, signum, frame):
        """Inmediately stop accepting new connections, and quit once there
        are not more ongoing requests.
        """
        # TODO Implement the graceful part

        # Quit
        print 'Shutting down the server (gracefully)...'
        if True:
            self.stop()


    def stop(self):
        self.main_loop.quit()


    #######################################################################
    # Request handling
    #######################################################################
    def star_callback(self, soup_message, path):
        method = soup_message.get_method()
        if method != 'OPTIONS':
            soup_message.set_status(405)
            soup_message.set_header('Allow', 'OPTIONS')
            return

        methods = self.app.known_methods
        soup_message.set_status(200)
        soup_message.set_header('Allow', ','.join(methods))


    def path_callback(self, soup_message, path):
        # 503 Service Unavailable
#       if len(self.connections) > MAX_CONNECTIONS:
#           soup_message.set_status(503)
#           soup_message.set_body('text/plain', '503 Service Unavailable')
#           return

        try:
            self._path_callback(soup_message, path)
        except Exception:
            self.log_error()
            soup_message.set_status(500)
            soup_message.set_body('text/plain', '500 Internal Server Error')


    def _path_callback(self, soup_message, path):
        context = self.context_class(soup_message, path)

        # 501 Not Implemented
        app = self.app
        if context.method not in app.known_methods:
            return context.set_response(501)

        # Step 1: Host
        app.find_host(context)

        # Step 2: Resource
        action = app.find_resource(context)
        if action == NOT_FOUND:
            return context.set_response(404) # 404 Not Found
        elif action == GONE:
            return context.set_response(410) # 410 Gone
        elif action == REDIRECT:
            context.set_status(307) # 307 Temporary redirect
            return context.set_header('Location', context.resource)
        elif action == MOVED:
            context.set_status(301) # 301 Moved Permanently
            return context.set_header('Location', context.resource)

        # 405 Method Not Allowed
        allowed_methods = app.get_allowed_methods(context)
        if context.method not in allowed_methods:
            context.set_response(405)
            return context.set_header('allow', ','.join(allowed_methods))

        # Step 3: User (authentication)
        action = app.find_user(context)
        if action == UNAUTHORIZED:
            return context.set_response(401) # 401 Unauthorized
        elif action == FORBIDDEN:
            return context.set_response(403) # 403 Forbidden

        # Continue
        method = app.known_methods[context.method]
        method = getattr(app, method)
        try:
            method(context)
        except HTTPError, exception:
            self.log_error()
            status = exception.code
            context.set_response(status)



###########################################################################
# For testing purposes
###########################################################################
if __name__ == '__main__':
    server = HTTPServer()
    print 'Start server..'
    server.start()

