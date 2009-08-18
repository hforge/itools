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
from signal import signal, SIGINT
from sys import stdout
from traceback import format_exc

# Import from pygobject
from gobject import MainLoop

# Import from itools
from itools.log import log_error
from itools.i18n import init_language_selector
from itools.uri import Path
from exceptions import HTTPError
from context import HTTPContext, set_context, set_response, select_language
from soup import SoupServer


# When the number of connections hits the maximum number of connections
# allowed, new connections will be automatically responded with the
# "503 Service Unavailable" error
MAX_CONNECTIONS = 50


class HTTPServer(SoupServer):

    # The default application says "hello"
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

        # Open access log
        if access_log is not None:
            self.access_log_file = open(access_log, 'a+')

        # Mounts (the link to the application code)
        self.mounts = [None, {}]


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


    #######################################################################
    # Start & Stop
    #######################################################################
    def start(self):
        # Language negotiation
        init_language_selector(select_language)

        # Graceful stop
        signal(SIGINT, self.stop_gracefully)
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
        if True:
            self.stop()


    def stop(self):
        self.main_loop.quit()
        if self.pid_file:
            remove_file(self.pid_file)
        if self.access_log:
            self.access_log_file.close()


    #######################################################################
    # Mounts
    #######################################################################
    def mount(self, path, mount):
        if type(path) is str:
            path = Path(path)

        aux = self.mounts
        for name in path:
            target, aux = aux.setdefault(name, [None, {}])
        aux[0] = mount


    def get_mount(self, path):
        mount, aux = self.mounts
        for name in path:
            aux = aux.get(name)
            if not aux:
                return mount
            if aux[0]:
                mount = aux[0]
            aux = aux[1]

        return mount


    #######################################################################
    # Callbacks
    #######################################################################
    known_methods = ['OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE']


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

        methods = self.known_methods
        soup_message.set_status(200)
        soup_message.set_header('Allow', ','.join(methods))


    def path_callback(self, soup_message, path):
        # 503 Service Unavailable
#       if len(self.connections) > MAX_CONNECTIONS:
#           return set_response(soup_message, 503)

        # New context
        try:
            context = self.context_class(soup_message, path)
        except Exception:
            log_error('Failed to make context instance', domain='itools.http')
            return set_response(soup_message, 500)

        # 501 Not Implemented
        if context.method not in self.known_methods:
            return set_response(soup_message, 501)

        # Mount
        mount = self.get_mount(context.path)
        if mount is None:
            return set_response(soup_message, 404)

        # Handle request
        set_context(context)
        context.mount = mount
        try:
            mount.handle_request(context)
        except Exception:
            log_error('Failed to handle request', domain='itools.http')
            set_response(soup_message, 500)
        finally:
            set_context(None)

