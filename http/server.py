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
from app import Application
from context import HTTPContext
from exceptions import HTTPError



class HTTPServer(SoupServer):

    # The default application says "hello"
    app = Application()
    context_class = HTTPContext


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
        try:
            self._path_callback(soup_message, path)
        except Exception:
            self.log_error()
            soup_message.set_status(500)
            soup_message.set_body('text/plain', '500 Internal Server Error')


    def _path_callback(self, soup_message, path):
        context = self.context_class(soup_message, path)

        # 501 Not Implemented
        method = context.get_method()
        method = method.lower()
        method = getattr(self, 'http_%s' % method, None)
        if method is None:
            return context.set_response(501)

        # Step 1: Host
        app = self.app
        app.get_host(context)

        # Step 2: Resource
        resource = app.get_resource(context)
        if resource is None:
            # 404 Not Found
            return context.set_response(404)
        if type(resource) is str:
            # 307 Temporary redirect
            context.set_status(307)
            context.set_header('Location', resource)
            return
        context.resource = resource

        # Step 3: User
        context.user = app.get_user(context)

        # Continue
        try:
            method(context)
        except HTTPError, exception:
            self.log_error()
            status = exception.code
            context.set_response(status)


    #######################################################################
    # Request methods
    def _get_server_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]


    def http_options(self, context):
        resource = context.resource

        # Methods supported by the server
        methods = self._get_server_methods()

        # Test capabilities of a resource
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
        context.set_status(200)
        context.set_header('Allow', ','.join(methods))


    def http_get(self, context):
        resource = context.resource

        # 405 Method Not Allowed
        method = getattr(resource, 'http_get', None)
        if method is None:
            context.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            context.set_header('allow', ','.join(methods))
            return

        # Continue
        return method(context)


    def http_post(self, context):
        resource = context.resource

        # 405 Method Not Allowed
        method = getattr(resource, 'http_post', None)
        if method is None:
            context.set_status(405)
            server_methods = set(self._get_server_methods())
            resource_methods = set(resource._get_reource_methods)
            methods = server_methods & resource_methods
            context.set_header('allow', ','.join(methods))
            return

        # Continue
        return method(context)


    http_head = http_get


###########################################################################
# For testing purposes
###########################################################################
if __name__ == '__main__':
    server = HTTPServer()
    print 'Start server..'
    server.start()

