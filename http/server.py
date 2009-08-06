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
from itools.uri import decode_query, Path
from app import Application
from exceptions import HTTPError
from headers import get_type
from response import get_response, status_messages


###########################################################################
# HTTP Message
###########################################################################

class HTTPMessage(object):

    def __init__(self, soup_message, path):
        self.soup_message = soup_message
        self.host = soup_message.get_host()
        self.path = Path(path)
        query = soup_message.get_query()
        self.query = decode_query(query)


    def get_header(self, name):
        name = name.lower()
        datatype = get_type(name)
        value = self.soup_message.get_header(name)
        return datatype.decode(value)


    def get_method(self):
        return self.soup_message.get_method()


    def get_referrer(self):
        return self.soup_message.get_header('referer')


    def set_header(self, name, value):
        name = name.lower()
        datatype = get_type(name)
        value = datatype.encode(value)
        self.soup_message.set_header(name, value)


    def set_response(self, content_type, body):
        self.soup_message.set_response(content_type, body)


    def set_status(self, status):
        self.soup_message.set_status(status)



###########################################################################
# HTTP Server
###########################################################################

class HTTPServer(SoupServer):

    # The default application says "hello"
    app = Application()


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
        # 501 Not Implemented
        method = soup_message.get_method()
        method = method.lower()
        method = getattr(self, 'http_%s' % method, None)
        if method is None:
            soup_message.set_status(501)
            soup_message.set_response('text/plain', '501 Not Implemented')
            return

        try:
            message = HTTPMessage(soup_message, path)
        except Exception:
            self.log_error()
            soup_message.set_status(500)
            soup_message.set_response('text/plain',
                                      '500 Internal Server Error')
            return

        try:
            method(message)
        except HTTPError, exception:
            self.log_error()
            status = exception.code
            reason = status_messages.get(status)
            soup_message.set_status(status)
            soup_message.set_response('text/plain', '%s %s' % (status, reason))
        except Exception:
            self.log_error()
            soup_message.set_status(500)
            soup_message.set_response('text/plain', '500 Internal Server Error')


    #######################################################################
    # Request methods
    def _get_server_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]


    def http_options(self, context):
        # Methods supported by the server
        methods = self._get_server_methods()

        # Test capabilities of a resource
        resource = self.app.get_resource(context.host, context.path)
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
        context.soup_message.set_status(200)
        context.set_header('Allow', ','.join(methods))


    def http_get(self, message):
        # Get the resource
        resource = self.app.get_resource(message.host, message.path)

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

        # 200 Ok
        return method(message)


    def http_post(self, message):
        # Get the resource
        resource = self.app.get_resource(message.host, message.path)

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


###########################################################################
# For testing purposes
###########################################################################
if __name__ == '__main__':
    server = HTTPServer()
    print 'Start server..'
    server.start()

