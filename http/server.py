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
from itools.uri import get_reference
from app import Application
from exceptions import HTTPError, BadRequest
from response import get_response, status_messages
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
        # 503 Service Unavailable
#       if len(self.connections) > MAX_CONNECTIONS:
#           message.set_status(503)
#           message.set_response('text/plain', '503 Service Unavailable')
#           return

        # 501 Not Implemented
        method = message.get_method()
        method = method.lower()
        method = getattr(self, 'http_%s' % method, None)
        if method is None:
            message.set_status(501)
            message.set_response('text/plain', '501 Not Implemented')
            return

        try:
            method(message, path)
        except HTTPError, exception:
            self.log_error()
            status = exception.code
            reason = status_messages.get(status)
            message.set_status(status)
            message.set_response('text/plain', '%s %s' % (status, reason))
        except Exception:
            self.log_error()
            message.set_status(500)
            message.set_response('text/plain', '500 Internal Server Error')


    #######################################################################
    # Request methods

    def _get_server_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]


    def http_options(self, message, path):
        # Methods supported by the server
        methods = self._get_server_methods()

        # Test capabilities of a resource
        if path != '*':
            uri = message.get_uri()
            uri = get_reference(uri)
            host = uri.authority
            resource = self.app.get_resource(host, path)
            resource_methods = resource._get_resource_methods()
            methods = set(methods) & set(resource_methods)
            # Special cases
            methods.add('OPTIONS')
            methods.add('TRACE')
            if 'GET' in methods:
                methods.add('HEAD')

        # Ok
        message.set_status(200)
        message.set_header('Allow', ','.join(methods))


    def http_get(self, message, path):
        # Get the resource
        uri = message.get_uri()
        uri = get_reference(uri)
        host = uri.authority
        resource = self.app.get_resource(host, path)

        # 404 Not Found
        if resource is None:
            return get_response(message, 404)

        # 302 Found
        if type(resource) is str:
            message.set_status(302)
            message.set_header('location', resource)
            return

        # 405 Method Not Allowed
        method = getattr(resource, 'http_get', None)
        if method is None:
            message.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            message.set_header('allow', ','.join(methods))
            return

        # Authorization (typically 401 Unauthorized)
#       realm = self.app.get_realm(resource.realm)
#       if realm.authenticate(request) is False:
#           return realm.challenge(request)

        # 200 Ok
        return method(message)


    def http_post(self, message, path):
        # Get the resource
        uri = message.get_uri()
        uri = get_reference(uri)
        host = uri.authority
        resource = self.app.get_resource(host, path)

        # 404 Not Found
        if resource is None:
            return get_response(message, 404)

        # 405 Method Not Allowed
        method = getattr(resource, 'http_post', None)
        if method is None:
            message.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            message.set_header('allow', ','.join(methods))
            return

        # Ok
        return method(message)


    http_head = http_get


    def http_trace(self, message, path):
        # TODO
        body = request.to_str()
        message.set_response('message/http', body)


###########################################################################
# For testing purposes
###########################################################################
if __name__ == '__main__':
    server = HTTPServer()
    print 'Start server..'
    server.start()

