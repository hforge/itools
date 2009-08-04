# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008-2009 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2009 Hervé Cauwelier <herve@itaapy.com>
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
from time import strftime, time
from traceback import format_exc

# Import from pygobject
from gobject import MainLoop, io_add_watch, source_remove

# Import from itools
from itools.log import log_error
from app import Application
from exceptions import HTTPError, BadRequest
from request import Request
from response import Response, get_response
from soup import SoupServer


# When the number of connections hits the maximum number of connections
# allowed, new connections will be automatically responded with the
# "503 Service Unavailable" error
MAX_CONNECTIONS = 50


class HTTPServer(SoupServer):

    # The default application says "hello"
    app = Application()


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
    def callback(self, message, path):
        try:
            self._callback(message, path)
        except Exception:
            self.log_error()
            message.set_status(500)
            message.set_response('text/plain', '500 Internal Server Error')


    def _callback(self, message, path):
        if path == '/':
            message.set_status(200)
            message.set_response('text/plain', 'Viva Fidel')
        else:
            message.set_status(404)
            message.set_response('text/plain', '404 Not Found')


    def handle_request(self, request):
        # 503 Service Unavailable
        if len(self.connections) > MAX_CONNECTIONS:
            return get_response(503)

        # 501 Not Implemented
        method = request.method.lower()
        method = getattr(self, 'http_%s' % method, None)
        if method is None:
            return get_response(501)

        # Go
        try:
            return method(request)
        except HTTPError, exception:
            self.log_error()
            return get_response(exception.code)
        except Exception:
            self.log_error()
            return get_response(500)


    #######################################################################
    # Request methods

    def _get_server_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]


    def http_options(self, request):
        # Methods supported by the server
        methods = self._get_server_methods()

        # Test capabilities of a resource
        uri = request.request_uri
        if uri != '*':
            host = request.get_host()
            resource = self.app.get_resource(host, uri)
            resource_methods = resource._get_resource_methods()
            methods = set(methods) & set(resource_methods)
            # Special cases
            methods.add('OPTIONS')
            methods.add('TRACE')
            if 'GET' in methods:
                methods.add('HEAD')

        # Ok
        response = Response()
        response.set_header('allow', ','.join(methods))
        return response


    def http_get(self, request):
        # Get the resource
        host = request.get_host()
        uri = request.request_uri
        resource = self.app.get_resource(host, uri)

        # 404 Not Found
        if resource is None:
            return get_response(404)

        # 302 Found
        if type(resource) is str:
            response = Response()
            response.set_status(302)
            response.set_header('location', resource)
            return response

        # 405 Method Not Allowed
        method = getattr(resource, 'http_get', None)
        if method is None:
            response = Response()
            response.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            response.set_header('allow', ','.join(methods))
            return response

        # Authorization (typically 401 Unauthorized)
        realm = self.app.get_realm(resource.realm)
        if realm.authenticate(request) is False:
            return realm.challenge(request)

        # 200 Ok
        return method(request)


    def http_post(self, request):
        # Get the resource
        host = request.get_host()
        uri = request.request_uri
        resource = self.app.get_resource(host, uri)

        # 404 Not Found
        if resource is None:
            return get_response(404)

        # 405 Method Not Allowed
        method = getattr(resource, 'http_post', None)
        if method is None:
            response = Response()
            response.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            response.set_header('allow', ','.join(methods))
            return response

        # Ok
        return method(request)


    def http_head(self, request):
        response = self.http_get(request)
        response.set_body(None)
        return response


    def http_trace(self, request):
        response = Response()
        response.set_header('content-type', 'message/http')
        response.set_body(request.to_str())
        return response


###########################################################################
# For testing purposes
###########################################################################
if __name__ == '__main__':
    server = HTTPServer()
    print 'Start server..'
    server.start()

