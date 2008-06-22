# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from os import fstat, getpid, remove as remove_file
from types import FunctionType, MethodType
from select import error as SelectError
from signal import signal, SIGINT
from socket import socket as Socket, error as SocketError
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import sys
from time import strftime
from traceback import print_exc
from types import GeneratorType
from urllib import unquote

# Import from itools
from itools.uri import Reference, Path
from itools.http import Request, Response, HTTPError
from itools.http import BadRequest, Forbidden, NotFound, Unauthorized
from itools.xml import XMLParser
from context import Context, get_context, set_context
from views import BaseView


# TODO Support multiple threads

###########################################################################
# Some pre-historic systems (e.g. Windows and MacOS) don't implement
# the "poll" sytem call. The code below is a wrapper around the "select"
# system call that implements the poll's API.
###########################################################################
POLLIN, POLLPRI, POLLOUT, POLLERR, POLLHUP, POLLNVAL = 1, 2, 4, 8, 16, 32
try:
    from select import poll as Poll
except ImportError:
    # Implement a wrapper around select with the API of poll
    from select import select
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
    """Offers a file-like interface for sockets in non-blocking mode.
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
        # This method is supposed to be called only when there is data to be
        # read. So if no data is available, we suppose the data is truncated
        # and we raise the EOFError exception.
        if not data:
            raise EOFError
        buffer += data
        # Check we now have the required data
        if len(buffer) >= size:
            data, self.buffer = buffer[:size], buffer[size:]
            return data
        # Could not read the required data
        self.buffer = buffer
        return None


    def readline(self):
        """This method is like the file object readline method, but not
        exactly.

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

    access_log = None
    error_log = None
    debug_log = None


    def __init__(self, root, address=None, port=None, access_log=None,
                 error_log=None, debug_log=None, pid_file=None):
        if address is None:
            address = ''
        if port is None:
            port = 8080
        # The application's root
        self.root = root
        # The address and port the server will listen to
        self.address = address
        self.port = port
        # Access log
        if access_log is not None:
            self.access_log_path = access_log
            self.access_log = open(access_log, 'a+')
        # Error log
        if error_log is None:
            self.error_log_path = None
            self.error_log = sys.stderr
        else:
            self.error_log_path = error_log
            self.error_log = open(error_log, 'a+')
        # Debug log
        if debug_log is not None:
            self.debug_log_path = debug_log
            self.debug_log = open(debug_log, 'a+')
        # The pid file
        self.pid_file = pid_file


    def start(self):
        if self.pid_file is not None:
            pid = getpid()
            open(self.pid_file, 'w').write(str(pid))

        ear = Socket(AF_INET, SOCK_STREAM)
        # Allow to reuse the address, this solves the bug "icms.py won't
        # close its connection properly". But is probably not the right
        # solution (FIXME).
        ear.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
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
                            except SocketError:
                                continue
                            # Debug
                            if self.debug_log is not None:
                                peer = conn.getpeername()
                                self.log_debug('%s:%s => New connection' % peer)
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
                            # Debug
                            if self.debug_log is not None:
                                peer = conn.getpeername()
                                self.log_debug('%s:%s => IN' % peer)
                            # Read
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
                            except BadRequest:
                                response = Response(status_code=400)
                                response.set_body('Bad Request')
                                # Log access
                                self.log_error()
                                self.log_access(conn, request, response)
                                # Ready to send response
                                poll.register(fileno, POLL_WRITE)
                                response = response.to_str()
                                requests[fileno] = conn, response
                            except:
                                self.log_error()
                                # FIXME Send a response to the client
                                # (BadRequest, etc.)?
                                conn.close()
                            else:
                                requests[fileno] = conn, request, loader
                                poll.register(fileno, POLL_READ)
                    elif event & POLLOUT:
                        poll.unregister(fileno)
                        conn, response = requests.pop(fileno)
                        # Debug
                        if self.debug_log is not None:
                            peer = conn.getpeername()
                            self.log_debug('%s:%s => OUT' % peer)
                        # Send the response
                        try:
                            n = conn.send(response)
                        except SocketError:
                            conn.close()
                        else:
                            response = response[n:]
                            if response:
                                poll.register(fileno, POLL_WRITE)
                                requests[fileno] = conn, response
                            else:
                                conn.close()
                    elif event & POLLERR:
                        self.log_debug('ERROR CONDITION')
                        poll.unregister(fileno)
                        if fileno in requests:
                            del requests[fileno]
                    elif event & POLLHUP:
                        self.log_debug('HUNG UP')
                        # XXX Is this right?
                        poll.unregister(fileno)
                        if fileno in requests:
                            del requests[fileno]
                    elif event & POLLNVAL:
                        self.log_debug('INVALID REQUEST (descriptor not open)')
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
            remove_file(self.pid_file)


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
        status, here, view, method = self.traverse(context)
        if status == 200:
            # Check modification time
            mtime = view.get_mtime(here)
            if mtime is not None:
                mtime = mtime.replace(microsecond=0)
                response.set_header('last-modified', mtime)
                if request.method == 'GET':
                    if request.has_header('if-modified-since'):
                        msince = request.get_header('if-modified-since')
                        if mtime <= msince:
                            return 304, None
        # Call the method
        try:
            body = method(here, context)
        except Forbidden:
            if context.user is None:
                status = 401
                body = context.site_root.unauthorized(context)
            else:
                status = 403
                body = context.root.forbidden(context)

        # Redirection
        if isinstance(body, Reference):
            return 302, body

        return status, body


    def HEAD(self, context):
        # Tweak the method to call if needed
        if context.method == 'HEAD':
            context.method = 'GET'
        # Do a GET
        return self.GET(context)


    def POST(self, context):
        request, response = context.request, context.response
        # Not a safe method
        context.commit = True
        # Traverse
        status, here, view, method = self.traverse(context)
        # Call the method
        try:
            body = method(here, context)
        except Forbidden:
            if context.user is None:
                status = 401
                body = context.site_root.unauthorized(context)
            else:
                status = 403
                body = context.root.forbidden(context)

        # Redirection
        if isinstance(body, Reference):
            return 302, body

        return status, body


    def PUT(self, context):
        context.commit = True
        # Traverse
        status, here, view, method = self.traverse(context)
        # Call the method
        body = method(context)
        return 204, None


    def LOCK(self, context):
        context.commit = True
        # Traverse
        status, here, view, method = self.traverse(context)
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
        status, here, view, method = self.traverse(context)
        # Call the method
        body = method(context)
        return 204, None


    def handle_request(self, request):
        context = Context(request)
        response = context.response
        # (1) Initialize the context
        context.init()
        context.server = self
        root = self.root
        context.root = root
        set_context(context)

        # (2) Perform the request method (GET, POST, ...)
        method = getattr(self, request.method)
        try:
            status, body = method(context)
        except:
            self.log_error(context)
            status = 500
            body = root.internal_server_error(context)

        # (3) Close the transaction (commit or abort)
        if status < 400 and context.commit is True:
            try:
                self.commit_transaction(context)
            except:
                self.log_error(context)
                status = 500
                body = root.internal_server_error(context)
        else:
            self.abort_transaction(context)

        # (4) Build response, when postponed (useful for POST methods)
        if isinstance(body, (FunctionType, MethodType)):
            try:
                body = body(context.object, context)
            except:
                self.log_error(context)
                status = 500
                body = root.internal_server_error(context)
            self.abort_transaction(context)

        # (5) Post-process (useful to wrap the body in a skin)
        if isinstance(body, (str, list, GeneratorType, XMLParser)):
            try:
                body = root.after_traverse(context, body)
            except:
                self.log_error(context)
                status = 500
                body = root.internal_server_error(context)

        # (6) If request is HEAD, do not return an entity
        if request.method == 'HEAD':
            if isinstance(body, str):
                # Set the content length, and body is None
                response.set_header('content-length', len(body))
                body = None

        # (7) Build and return the response
        if body is None:
            response.set_body(body)
        elif isinstance(body, str):
            response.set_body(body)
        elif isinstance(body, Reference):
            context.redirect(body)
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
        """Returns the status code (200 if everything is Ok so far) and
        the method to call.
        """
        root = context.root
        root.init(context)
        user = context.user = self.get_user(context)
        site_root = self.get_site_root(context.uri.authority.host)
        site_root.before_traverse(context)
        context.site_root = site_root

        # Get the object
        path = str(context.path)
        if path[0] == '/':
            path = path[1:]
            if path == '':
                path = '.'
        try:
            here = site_root.get_object(path)
        except LookupError:
            here = None

        if here is None:
            # Find an ancestor to render the page
            abspath = Path(path)
            for x in range(len(abspath) - 1, 0, -1):
                path = abspath[:x]
                try:
                    here = site_root.get_object(path)
                except LookupError:
                    continue
                else:
                    break
            else:
                here = site_root
            context.object = here
            view = root.get_view('not_found')
            return 404, here, view, view.GET

        context.object = here

        # Get the view
        query = context.uri.query
        view = here.get_view(context.method, **query)
        if view is None:
            view = root.get_view('not_found')
            return 404, here, view, view.GET

        # Check security
        ac = here.get_access_control()
        if not ac.is_access_allowed(user, here, view):
            # Unauthorized
            if user is None:
                view = site_root.get_view('unauthorized')
                return 401, here, view, view.GET
            # Forbidden
            view = site_root.get_view('forbidden')
            return 403, here, view, view.GET

        # Get the method
        method = getattr(view, context.request.method, None)
        if method is None:
            # FIXME For HTTP 1.1 this should be "405 Method not Allowed"
            view = site_root.get_view('forbidden')
            return 403, here, view, view.GET

        # OK
        return 200, here, view, method


    def abort_transaction(self, context):
        for db in self.get_databases():
            db.abort_changes()


    def commit_transaction(self, context):
        try:
            self.before_commit()
        except:
            self.log_error(context)
            self.abort_transaction(context)
        else:
            for db in self.get_databases():
                db.save_changes()


    ########################################################################
    # Logging
    ########################################################################
    def log_access(self, conn, request, response):
        # Common Log Format
        #  - IP address of the client
        #  - RFC 1413 identity (not available)
        #  - username (XXX not provided right now, should we?)
        #  - time (XXX we use the timezone name, while we should use the
        #    offset, e.g. +0100)
        #  - the request line
        #  - the status code
        #  - content length of the response
        log = self.access_log
        if log is None:
            return

        # The data to write
        host, port = conn.getpeername()
        namespace = (host, strftime('%d/%b/%Y:%H:%M:%S %Z'),
                     request.request_line, response.status,
                     response.get_content_length())
        data = '%s - - [%s] "%s" %s %s\n' % namespace

        # Check the file has not been removed
        if fstat(log.fileno())[3] == 0:
            log = open(self.access_log_path, 'a+')
            self.access_log = log

        # Write
        log.write(data)
        log.flush()


    def log_error(self, context=None):
        log = self.error_log
        if log is None:
            return

        # The separator
        lines = []
        lines.append('\n')
        lines.append('%s\n' % ('*' * 78))
        # The date
        lines.append('DATE: %s\n' % datetime.now())
        # The request data
        if context is not None:
            # The URI and user
            user = context.user
            lines.append('URI : %s\n' % str(context.uri))
            lines.append('USER: %s\n' % (user and user.name or None))
            lines.append('\n')
            # The request
            request = context.request
            lines.append(request.request_line_to_str())
            lines.append(request.headers_to_str())
        lines.append('\n')
        data = ''.join(lines)

        # Check the file has not been removed
        if fstat(log.fileno())[3] == 0:
            log = open(self.error_log_path, 'a+')
            self.error_log = log

        # Write
        log.write(data)
        print_exc(file=log) # FIXME Should be done before to reduce the risk
                            # of the log file being removed.
        log.flush()


    def log_debug(self, message):
        log = self.debug_log
        if log is None:
            return

        # The data to write
        data = '%s %s\n' % (datetime.now(), message)

        # Check the file has not been removed
        if fstat(log.fileno())[3] == 0:
            log = open(self.debug_log_path, 'a+')
            self.debug_log = log

        # Write
        log.write(data)
        log.flush()


    ########################################################################
    # Hooks (to be overriden)
    ########################################################################
    def get_databases(self):
        return []


    def before_commit(self):
        pass


    def get_site_root(self, hostname):
        return self.root

