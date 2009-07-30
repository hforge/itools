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
from cProfile import runctx
from os import fstat, getpid, remove as remove_file
from signal import signal, SIGINT, SIGTERM
from sys import stdout

# Import from pygobject
from gobject import MainLoop

# Import from itools
from itools.i18n import init_language_selector
from itools.soup import SoupServer
from response import Response, get_response


class HTTPServer(SoupServer):

    app = None


    def __init__(self, address='', port=8080, access_log=None, pid_file=None,
                 profile=None):
        SoupServer.__init__(self, address=address, port=port)

        # Keep arguments
        self.address = address
        self.port = port
        self.access_log = access_log
        self.pid_file = pid_file
        self.profile = profile

        # Main Loop
        self.main_loop = MainLoop()

        # Open log files
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


    #######################################################################
    # Start & Stop
    #######################################################################
    def start(self):
        # Language negotiation
        from itools.web import select_language
        init_language_selector(select_language)

        # Graceful stop
        signal(SIGINT, self.stop_gracefully)
        signal(SIGTERM, self.zap)
        if self.pid_file:
            pid = getpid()
            open(self.pid_file, 'w').write(str(pid))

        # Run
        SoupServer.start(self)
        print 'Listen %s:%d' % (self.address, self.port)
        if self.profile:
            runctx("self.main_loop.run()", globals(), locals(), self.profile)
        else:
            self.main_loop.run()


    def stop_gracefully(self, signum, frame):
        """Inmediately stop accepting new connections, and quit once there
        are not more ongoing requests.
        """
        # TODO Implement the graceful part

        # Quit
        print 'Shutting down the server (gracefully)...'
        self.stop()


    def zap(self, signum, frame):
        print 'Shutting down the server...'
        self.stop()


    def stop(self):
        SoupServer.stop(self)
        self.main_loop.quit()
        if self.pid_file:
            remove_file(self.pid_file)
        if self.access_log:
            self.access_log_file.close()


    #######################################################################
    # Callbacks
    #######################################################################
    def star_callback(self, soup_message, path):
        """This method is called for the special "*" request URI, which means
        the request concerns the server itself, and not any particular
        resource.

        Currently this feature is only supported for the OPTIONS request
        method:

          OPTIONS * HTTP/1.1
        """
        method = soup_message.get_method()
        if method != 'OPTIONS':
            soup_message.set_status(405)
            soup_message.set_header('Allow', 'OPTIONS')
            return

        methods = self._get_server_methods()
        soup_message.set_status(200)
        soup_message.set_header('Allow', ','.join(methods))


    def path_callback(self, soup_message, path):
        raise NotImplementedError


    #######################################################################
    # Request methods
    def _get_server_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]


    def http_options(self, context):
        # Methods supported by the server
        methods = self._get_server_methods()

        # Test capabilities of a resource
        resource = self.app.get_resource(context.uri.authority, context.path)
        resource_methods = resource._get_resource_methods()
        methods = set(methods) & set(resource_methods)
        # Special cases
        methods.add('OPTIONS')
        if 'GET' in methods:
            methods.add('HEAD')
        # DELETE is unsupported at the root
        if context.path == '/':
            methods.discard('DELETE')

        # Ok
        context.set_header('allow', ','.join(methods))
        context.soup_message.set_status(200)


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

