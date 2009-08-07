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
from exceptions import HTTPError
from message import HTTPMessage
from soup import SoupServer


# When the number of connections hits the maximum number of connections
# allowed, new connections will be automatically responded with the
# "503 Service Unavailable" error
MAX_CONNECTIONS = 50


class HTTPServer(SoupServer):

    # The default application says "hello"
    app = Application()
    message_class = HTTPMessage


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

        methods = self._get_server_methods()
        soup_message.set_status(200)
        soup_message.set_header('Allow', ','.join(methods))


    def path_callback(self, soup_message, path):
        # 503 Service Unavailable
#       if len(self.connections) > MAX_CONNECTIONS:
#           return message.set_response(503)

        try:
            self._path_callback(soup_message, path)
        except Exception:
            self.log_error()
            soup_message.set_status(500)
            soup_message.set_body('text/plain', '500 Internal Server Error')


    def _path_callback(self, soup_message, path):
        message = self.message_class(soup_message, path)

        # 501 Not Implemented
        method = message.get_method()
        method = method.lower()
        method = getattr(self, 'http_%s' % method, None)
        if method is None:
            return message.set_response(501)

        # Get the resource
        resource = self.app.get_resource(message.host, path)
        # 404 Not Found
        if resource is None:
            return message.set_response(404)
        # 307 Temporary redirect
        if type(resource) is str:
            message.set_status(307)
            message.set_header('Location', resource)
            return

        # Continue
        message.resource = resource
        try:
            method(message)
        except HTTPError, exception:
            self.log_error()
            status = exception.code
            message.set_response(status)


    #######################################################################
    # Request methods

    def _get_server_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]


    def http_options(self, message):
        resource = message.resource

        # Methods supported by the server
        methods = self._get_server_methods()

        # Test capabilities of a resource
        path = message.path
        host = message.host
        resource_methods = resource._get_resource_methods()
        methods = set(methods) & set(resource_methods)
        # Special cases
        methods.add('OPTIONS')
        if 'GET' in methods:
            methods.add('HEAD')

        # Ok
        message.set_status(200)
        message.set_header('Allow', ','.join(methods))


    def http_get(self, message):
        resource = message.resource

        # 405 Method Not Allowed
        method = getattr(resource, 'http_get', None)
        if method is None:
            message.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            message.set_header('allow', ','.join(methods))
            return

        # Continue
        return method(message)


    def http_post(self, message):
        resource = message.resource

        # 405 Method Not Allowed
        method = getattr(resource, 'http_post', None)
        if method is None:
            message.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            message.set_header('allow', ','.join(methods))
            return

        # Continue
        return method(message)


    http_head = http_get


#   def http_trace(self, message):
#       # TODO
#       body = request.to_str()
#       message.set_body('message/http', body)


###########################################################################
# For testing purposes
###########################################################################
if __name__ == '__main__':
    server = HTTPServer()
    print 'Start server..'
    server.start()

