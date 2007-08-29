# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
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
from base64 import decodestring
from copy import copy
from datetime import datetime
import os
from select import error as SelectError
from signal import signal, SIGINT
import socket
import sys
import time
import traceback
from urllib import unquote

# Import from itools
from itools.uri import Reference
from itools.http import (Forbidden, HTTPError, NotFound, Unauthorized,
                         Request, Response)
from context import Context, get_context, set_context
from base import Node


###########################################################################
# Some pre-historic systems (e.g. Windows and MacOS) don't implement
# the "poll" sytem call. The code below is a wrapper around the "select"
# system call that implements the poll's API.
###########################################################################
POLLIN, POLLPRI, POLLOUT, POLLERR, POLLHUP, POLLNVAL = 1, 2, 4, 8, 16, 32
try:
    from select import poll as Poll
except ImportError:
    from select import select
    # TODO: implement a wrapper around select with the API of poll
    class Poll(object):
        def __init__(self):
            self.iwtd, self.owtd, self.ewtd = [], [], []

        def register(self, fileno, mode):
            if mode & POLLIN or mode & POLLPRI:
                self.iwtd.append(fileno)
            if mode & POLLOUT:
                self.owtd.append(fileno)
            if mode & POLLERR or mode & POLLHUP or mode & POLLNVAL:
                self.ewtd.append(fileno)

        def unregister(self, fileno):
            for wtd in self.iwtd, self.owtd, self.ewtd:
                if fileno in wtd:
                    wtd.remove(fileno)
        
        def poll(self):
            iwtd, owtd, ewtd = select(self.iwtd, self.owtd, self.ewtd)
            return [ (x, POLLIN) for x in iwtd ] \
                   + [ (x, POLLOUT) for x in owtd ] \
                   + [ (x, POLLERR) for x in ewtd ]



###########################################################################
# Wrapper around sockets in non-blocking mode that offers the a file
# like API
###########################################################################
class SocketWrapper(object):
    """
    Offers a file-like interface for sockets in non-blocking mode.
    Read only.
    """

    __slots__ = ['socket', 'buffer']

    def __init__(self, socket):
        self.socket = socket
        self.buffer = ''


    def read(self, size):
        buffer = self.buffer
        buffer_size = len(buffer)
        # Check we already have the required data
        if buffer_size >= size:
            data, self.buffer = buffer[:size], buffer[size:]
            return data
        # Try to read the remaining
        try: 
            data = self.socket.recv(size - buffer_size)
        except:
            return None
        buffer += data
        # Check we now have the required data
        if len(buffer) >= size:
            data, self.buffer = buffer[:size], buffer[size:]
            return data
        # Could not read the required data
        self.buffer = buffer
        return None


    def readline(self):
        """
        This method is like the file object readline method, but not exactly.

        Written specifically for the HTTP protocol, it expects the sequence
        '\r\n' to signal line ending.

        This method is supposed to be called only when there is data to be
        read. So if no data is available, we suppose the line is truncated
        and we raise the EOFError exception.

        If the end-of-line sequence was not being received the value None
        is returned, what means: call me again when more data is available.
        """
        # FIXME Try to make it more like the file interface.
        buffer = self.buffer
        # Check if there is already a line in the buffer
        if '\r\n' in buffer:
            line, self.buffer = buffer.split('\r\n', 1)
            return line
        # Read as much as possible
        recv = self.socket.recv
        # FIXME Here we assume that if the call to "recv" fails is because
        # there is no data available, and we should try again later. But
        # the failure maybe for something else. So we must do proper error
        # handling here. Check http://docs.python.org/lib/module-errno.html
        # for a list of the possible errors.
        try:
            data = recv(512)
        except:
            return None
        if not data:
            raise EOFError
        while data:
            buffer += data
            # Hit
            if '\r\n' in buffer:
                line, self.buffer = buffer.split('\r\n', 1)
                return line
            # Miss
            if len(data) < 512:
                self.buffer = buffer
                return None 
            # FIXME Catch only the relevant exceptions (see note above)
            try:
                data = recv(512)
            except:
                return None


###########################################################################
# The Web Server
###########################################################################
class Server(object):

    def __init__(self, root, address=None, port=None, access_log=None,
                 error_log=sys.stderr, pid_file=None):
        if address is None:
            address = ''
        if port is None:
            port = 8080
        # The application's root
        self.root = root
        # The address and port the server will listen to
        self.address = address
        self.port = port
        # The access log
        if isinstance(access_log, str):
            access_log = open(access_log, 'a+')
        self.access_log = access_log
        # The error log
        if isinstance(error_log, str):
            error_log = open(error_log, 'a+')
        self.error_log = error_log
        # The pid file
        self.pid_file = pid_file


    def start(self):
        if self.pid_file is not None:
            pid = os.getpid()
            open(self.pid_file, 'w').write(str(pid))

        ear = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow to reuse the address, this solves the bug "icms.py won't
        # close its connection properly". But is probably not the right
        # solution (XXX).
        ear.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ear.bind((self.address, self.port))
        ear.listen(5)
        ear_fileno = ear.fileno()

        # Mapping {<fileno>: (request, loader)}
        requests = {ear_fileno: None}

        # Set-up polling object
        POLL_READ = POLLIN | POLLPRI | POLLERR | POLLHUP | POLLNVAL
        POLL_WRITE = POLLOUT | POLLERR | POLLHUP | POLLNVAL
        poll = Poll()
        poll.register(ear_fileno, POLL_READ)

        # Set up the graceful stop
        def stop(n, frame, ear=ear, ear_fileno=ear_fileno, poll=poll,
                 requests=requests):
            if ear_fileno not in requests:
                return
            poll.unregister(ear_fileno)
            ear.close()
            requests.pop(ear_fileno)
            print 'Shutting down the server (gracefully)...'
        signal(SIGINT, stop)

        # Loop
        while requests:
            try:
                for fileno, event in poll.poll():
                    if event & POLLIN or event & POLLPRI:
                        if fileno == ear_fileno:
                            # New request
                            try:
                                conn, client_address = ear.accept()
                            except socket.error:
                                continue

                            # Set non-blocking mode
                            conn.setblocking(0)
                            # Register the connection
                            fileno = conn.fileno()
                            poll.register(fileno, POLL_READ)
                            # Build and store the request
                            request = Request()
                            wrapper = SocketWrapper(conn)
                            loader = request.non_blocking_load(wrapper)
                            requests[fileno] = conn, request, loader
                        else:
                            # Load request
                            poll.unregister(fileno)
                            conn, request, loader = requests.pop(fileno)
                            try:
                                loader.next()
                            except StopIteration:
                                response = self.handle_request(request)
                                # Log access
                                self.log_access(conn, request, response)
                                # Ready to send response
                                poll.register(fileno, POLL_WRITE)
                                response = response.to_str()
                                requests[fileno] = conn, response
                            except:
                                self.log_error()
                                # XXX Send a response to the client
                                # (BadRequest, etc.)?
                                conn.close()
                            else:
                                requests[fileno] = conn, request, loader
                                poll.register(fileno, POLL_READ)
                    elif event & POLLOUT:
                        poll.unregister(fileno)
                        conn, response = requests.pop(fileno)
                        # Send the response
                        n = conn.send(response)
                        response = response[n:]
                        if response:
                            poll.register(fileno, POLL_WRITE)
                            requests[fileno] = conn, response
                        else:
                            conn.close()
                    elif event & POLLERR:
                        poll.unregister(fileno)
                        if fileno in requests:
                            del requests[fileno]
                    elif event & POLLHUP:
                        # XXX Is this right?
                        poll.unregister(fileno)
                        if fileno in requests:
                            del requests[fileno]
                    elif event & POLLNVAL:
                        # XXX Is this right?
                        poll.unregister(fileno)
                        if fileno in requests:
                            del requests[fileno]
            except SelectError, exception:
                # Don't log an error every time the server is stopped
                # (check "perror 4" from the shell)
                errno, kk = exception
                if errno != 4:
                    self.log_error()
            except:
                self.log_error()

        # Close files
        if self.access_log is not None:
            self.access_log.close()
        if self.error_log is not None:
            self.error_log.close()
        # Remove pid file
        if self.pid_file is not None:
            os.remove(self.pid_file)


    ########################################################################
    # Handle a request
    ########################################################################
    def GET(self, context):
        request, response = context.request, context.response
        # This is a safe method
        context.commit = False
        # Our canonical URLs never end with an slash
        if context.uri.path.endswith_slash:
            goto = copy(context.uri)
            goto.path.endswith_slash = False
            return 302, goto
        # Traverse
        status, method = self.traverse(context)
        if status == 200:
            # Check modification time
            mtime = getattr(context.handler, '%s__mtime__' % context.method, None)
            if mtime is not None:
                mtime = mtime().replace(microsecond=0)
                response.set_header('last-modified', mtime)
                if request.method == 'GET':
                    if request.has_header('if-modified-since'):
                        msince = request.get_header('if-modified-since')
                        if mtime <= msince:
                            return 304, None
        # Call the method
        try:
            body = method(context) 
        except Forbidden:
            if context.user is None:
                status = 401
                body = context.root.unauthorized(context)
            else:
                status = 403
                body = context.root.forbidden(context)

        # Redirection
        if isinstance(body, Reference):
            return 302, body
        # XXX
        if body is None:
            return status, body

        # Post-process (used to wrap the body in a skin)
        body = context.root.after_traverse(context, body)
        return status, body


    def HEAD(self, context):
        # Tweak the method to call if needed
        if context.method == 'HEAD':
            context.method = 'GET'
        # Do a GET
        status, body = self.GET(context)
        # Set the content length, and body is None
        # XXX This may not work correctly if body is not a string
        if isinstance(body, str):
            response = context.response
            response.set_header('content-length', len(body))
            body = None

        return status, body


    def POST(self, context):
        request, response = context.request, context.response
        # Not a safe method
        context.commit = True
        # Traverse
        status, method = self.traverse(context)
        # Call the method
        try:
            body = method(context) 
        except Forbidden:
            if context.user is None:
                status = 401
                body = context.root.unauthorized(context)
            else:
                status = 403
                body = context.root.forbidden(context)

        # Redirection
        if isinstance(body, Reference):
            return 302, body
        # XXX
        if body is None:
            return status, body

        # Post-process (used to wrap the body in a skin)
        body = context.root.after_traverse(context, body)
        return status, body


    def PUT(self, context):
        context.commit = True
        # Traverse
        status, method = self.traverse(context)
        # Call the method
        body = method(context) 
        return 204, None


    def LOCK(self, context):
        context.commit = True
        # Traverse
        status, method = self.traverse(context)
        # Call the method
        body = method(context) 
        if isinstance(body, str):
            return 200, body
        elif body is None:
            return 423, None
        raise TypeError


    def UNLOCK(self, context):
        context.commit = True
        # Traverse
        status, method = self.traverse(context)
        # Call the method
        body = method(context) 
        return 204, None


    def handle_request(self, request):
        context = Context(request)
        response = context.response
        # Initialize the context
        context.init()
        context.server = self
        context.root = self.root
        set_context(context)

        # Get and call the method
        method = getattr(self, request.method)
        try:
            status, body = method(context)
        except:
            self.log_error(context)
            status = 500
            body = self.root.internal_server_error(context)

        # Be sure not to commit on errors
        if status >= 400:
            context.commit = False

        # Commit
        try:
            self.commit_transaction(context)
        except:
            self.log_error(context)
            status = 500
            body = self.root.internal_server_error(context)

        # Set body
        if isinstance(body, str):
            response.set_body(body)
        elif isinstance(body, Reference):
            context.redirect(body)

        # Set status
        response.set_status(status)
        return response


    ########################################################################
    # Stages
    def get_user(self, context):
        # Check the id/auth cookie
        cookie = context.get_cookie('__ac')
        if cookie is None:
            return None

        # Process cookie
        cookie = unquote(cookie)
        cookie = decodestring(cookie)
        username, password = cookie.split(':', 1)

        # Check user exists
        user = context.root.get_user(username)
        if user is None:
            return None

        # Authenticate
        if user.authenticate(password):
            return user

        return None


    def traverse(self, context):
        """
        Returns the status code (200 if everything is Ok so far) and
        the method to call.
        """
        root = context.root
        root.init(context)
        user = context.user = self.get_user(context)
        root.before_traverse(context)
        site_root = self.get_site_root(context.uri.authority.host)
        context.site_root = site_root
        # Traverse
        path = str(context.path)
        if not context.request.has_header('X-Base-Path'):
            if path[0] == '/':
                path = path[1:]
                if path == '':
                    path = '.'
        try:
            handler = site_root.get_handler(path)
        except LookupError:
            handler = None
        context.handler = handler

        if not isinstance(handler, Node):
            # Find an ancestor to render the page
            abspath = context.path
            for x in range(len(abspath) - 1, 0, -1):
                path = abspath[:x]
                if root.has_handler(path):
                    context.handler = root.get_handler(path)
                    break
            else:
                context.handler = root
            return 404, root.not_found

        method = handler.get_method(context.method)
        if method is None:
            return 404, root.not_found
        # Check security
        ac = handler.get_access_control()
        if ac.is_access_allowed(user, handler, context.method):
            return 200, method
        # Not allowed
        if user is None:
            return 401, root.unauthorized
        return 403, root.forbidden


    def commit_transaction(self, context):
        databases = self.get_databases()

        # Abort transaction if code says so
        if context.commit is False:
            for db in databases:
                db.abort()
            return

        # Before commit (hook)
        self.before_commit()

        # Commit
        for db in databases:
            db.commit()


    ########################################################################
    # Logging
    ########################################################################
    def log_access(self, conn, request, response):
        # Common Log Format
        #  - IP address of the client
        #  - RFC 1413 identity (not available)
        #  - username (XXX not provided right now should we?)
        #  - time (XXX we use the timezone name, while we should use the
        #    offset, e.g. +0100)
        #  - the request line
        #  - the status code
        #  - content length of the response
        log = self.access_log
        if log is not None:
            host, port = conn.getpeername()
            namespace = (host, time.strftime('%d/%b/%Y:%H:%M:%S %Z'),
                         request.request_line, response.status,
                         response.get_content_length())
            log.write('%s - - [%s] "%s" %s %s\n' % namespace)
            log.flush()


    def log_error(self, context=None):
        # TODO This method may be called from different threads, lock
        log = self.error_log
        if log is not None:
            # The separator
            log.write('\n')
            log.write('%s\n' % ('*' * 78))
            # The date
            log.write('DATE: %s\n' % datetime.now())
            # The request data
            if context is not None:
                # The URI and user
                user = context.user
                log.write('URI : %s\n' % str(context.uri))
                log.write('USER: %s\n' % (user and user.name or None))
                log.write('\n')
                # The request
                request = context.request
                log.write(request.request_line_to_str())
                log.write(request.headers_to_str())

            # The traceback
            log.write('\n')
            traceback.print_exc(file=log)
            log.flush()


    ########################################################################
    # Hooks (to be overriden)
    ########################################################################
    def get_databases(self):
        return []


    def before_commit(self):
        pass


    def get_site_root(self, hostname):
        raise NotImplementedError

