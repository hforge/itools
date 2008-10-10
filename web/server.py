# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007-2008 Henry Obein <henry@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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
from urllib import unquote

# Import from itools
from itools.http import Request, Response, ClientError, NotModified
from itools.http import BadRequest, Forbidden, NotFound, Unauthorized
from itools.i18n import init_language_selector
from itools.uri import Reference, Path
from context import Context, get_context, set_context, select_language
from context import FormError
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
# Wrapper around sockets in non-blocking mode that offers a file
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
                 error_log=None, debug_log=None, pid_file=None,
                 auth_type='cookie', auth_realm='Restricted Area'):
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
        # Authentication options
        self.auth_type = auth_type
        self.auth_realm = auth_realm


    def start(self):
        # Language negotiation
        init_language_selector(select_language)

        # PID file
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


    #######################################################################
    # Stage 0: Initialize the context
    #######################################################################
    def init_context(self, context):
        # (1) Initialize the response status to None, it will be changed
        # through the request handling process.
        context.status = None

        # (2) The server, the data root and the authenticated user
        context.server = self
        context.root = self.root

        # (3) The authenticated user
        self.find_user(context)

        # (4) The Site Root
        self.find_site_root(context)
        context.site_root.before_traverse(context)  # Hook

        # (5) Keep the context
        set_context(context)


    def find_user(self, context):
        context.user = None

        # (1) Choose the Authentication method
        if self.auth_type == 'cookie':
            # (1bis) Read the id/auth cookie
            cookie = context.get_cookie('__ac')
            if cookie is None:
                return

            cookie = unquote(cookie)
            cookie = decodestring(cookie)
            username, password = cookie.split(':', 1)
        elif self.auth_type == 'http_basic':
            # (1bis) Read the username/password from header
            authorization = context.request.get_header('Authorization')
            if authorization is None:
                return

            # Basic Authentication
            method, value = authorization
            if method != 'basic':
                raise BadRequest, 'XXX'
            username, password = value

        if username is None or password is None:
            return

        # (2) Get the user resource and authenticate
        user = context.root.get_user(username)
        if user is not None and user.authenticate(password):
            context.user = user


    def find_site_root(self, context):
        """This method may be overriden to support virtual hosting.
        """
        context.site_root = self.root


    ########################################################################
    # Request handling: main functions
    ########################################################################
    def handle_request(self, request):
        # (1) Get the class that will handle the request
        method = methods.get(request.method)
        if method is None:
            # FIXME Return the right response
            message = 'the request method "%s" is not implemented'
            raise NotImplementedError, message % request.method

        # (2) Initialize the context
        context = Context(request)
        self.init_context(context)

        # (3) Pass control to the Get method class
        method.handle_request(self, context)

        # (4) Return the response
        return context.response


    def abort_transaction(self, context):
        for db in self.get_databases():
            db.abort_changes()



###########################################################################
# The Request Methods
###########################################################################

class RequestMethod(object):

    @classmethod
    def find_resource(cls, server, context):
        """Sets 'context.resource' to the requested resource if it exists.

        Otherwise sets 'context.status' to 404 (not found error) and
        'context.resource' to the latest resource in the path that does exist.
        """
        resource = context.site_root
        for name in context.path:
            try:
                resource = resource.get_resource(name)
            except LookupError:
                context.resource = resource
                raise NotFound

        context.resource = resource


    @classmethod
    def find_view(cls, server, context):
        query = context.uri.query
        context.view = context.resource.get_view(context.view_name, query)
        if context.view is None:
            raise NotFound


    @classmethod
    def check_access(cls, server, context):
        """Tell whether the user is allowed to access the view on the
        resource.
        """
        user = context.user
        resource = context.resource
        view = context.view

        # Get the check-point
        ac = resource.get_access_control()
        if ac.is_access_allowed(user, resource, view):
            return

        # Unauthorized (401)
        if user is None:
            raise Unauthorized

        # Forbidden (403)
        raise Forbidden


    @classmethod
    def commit_transaction(cls, server, context):
        # Hook: before commit
        try:
            server.before_commit()
        except:
            cls.internal_server_error(server, context)
            server.abort_transaction(context)
            return

        # Commit
        try:
            for db in server.get_databases():
                db.save_changes()
        except:
            cls.internal_server_error(server, context)


    @classmethod
    def set_body(cls, server, context):
        response = context.response
        body = context.entity
        if body is None:
            response.set_body(body)
        elif isinstance(body, str):
            response.set_header('content-length', len(body))
            response.set_body(body)
        elif isinstance(body, Reference):
            context.redirect(body)


    @classmethod
    def internal_server_error(cls, server, context):
        server.log_error(context)
        context.status = 500
        context.entity = server.root.internal_server_error(context)



status2name = {
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    405: 'forbidden',
}


class GET(RequestMethod):

    @classmethod
    def check_method(cls, server, context):
        # Get the method
        method = getattr(context.view, 'GET', None)
        if method is None:
            raise MethodNotAllowed

        context.view_method = method


    @classmethod
    def handle_request(cls, server, context):
        response = context.response
        root = context.root

        # (1) Find out the requested resource and view
        try:
            # The requested resource and view
            cls.find_resource(server, context)
            cls.find_view(server, context)
            # Access Control
            cls.check_access(server, context)
            # Check the request method is supported
            cls.check_method(server, context)
            # Check the client's cache
            cls.check_cache(server, context)
        except Unauthorized, error:
            status = error.code
            context.status = status
            context.view_name = status2name[status]
            context.view = root.get_view(context.view_name)
            if server.auth_type == 'http_basic':
                basic_header = 'Basic realm="%s"' % server.auth_realm
                response.set_header('WWW-Authenticate', basic_header)
        except ClientError, error:
            status = error.code
            context.status = status
            context.view_name = status2name[status]
            context.view = root.get_view(context.view_name)
        except NotModified:
            response.set_status(304)
            response.set_header('content-length', 0)
            response.set_body(None)
            return response
        else:
            # Everything goes fine so far
            context.status = 200

        # (2) Always deserialize the query
        resource = context.resource
        view = context.view
        try:
            context.query = view.get_query(context)
        except FormError, error:
            method = view.on_query_error
            context.query_error = error
        except:
            cls.internal_server_error(server, context)
            method = None
        else:
            method = view.GET

        # (3) Render
        if method is not None:
            try:
                context.entity = method(resource, context)
            except:
                cls.internal_server_error(server, context)
            else:
                # Ok: set status
                if isinstance(context.entity, Reference):
                    context.status = 302

        # (4) Reset the transaction in any case
        server.abort_transaction(context)

        # (5) After Traverse hook
        try:
            context.site_root.after_traverse(context)
        except:
            cls.internal_server_error(server, context)

        # (6) Build and return the response
        context.response.set_status(context.status)
        cls.set_body(server, context)

        # (7) Ok
        return context.response


    @classmethod
    def check_cache(cls, server, context):
        # Get the resource's modification time
        resource = context.resource
        mtime = context.view.get_mtime(resource)
        if mtime is None:
            return

        # Set the last-modified header
        mtime = mtime.replace(microsecond=0)
        context.response.set_header('last-modified', mtime)

        # Check for the request header If-Modified-Since
        if_modified_since = context.request.get_header('if-modified-since')
        if if_modified_since is None:
            return

        # Cache: check modification time
        if mtime <= if_modified_since:
            raise NotModified



class HEAD(GET):

    @classmethod
    def set_body(cls, server, context):
        GET.set_body(server, context)
        # Drop the body from the response
        context.response.set_body(None)



class POST(RequestMethod):

    @classmethod
    def check_method(cls, server, context):
        # If there was an error, the method name always will be 'GET'
        if context.status is None:
            method_name = 'POST'
        else:
            method_name = 'GET'

        # Get the method
        method = getattr(context.view, method_name, None)
        if method is not None:
            context.view_method = method
            return

        # Method not allowed
        # FIXME For HTTP 1.1 this should be "405 Method not Allowed"
        context.status = 403
        context.view_name = 'forbidden'
        context.view = context.site_root.get_view(context.view_name)
        context.view_method = context.view.GET


    @classmethod
    def handle_request(cls, server, context):
        response = context.response
        root = context.root

        # (1) Find out the requested resource and view
        try:
            # The requested resource and view
            cls.find_resource(server, context)
            cls.find_view(server, context)
            # Access Control
            cls.check_access(server, context)
            # Check the request method is supported
            cls.check_method(server, context)
        except Unauthorized, error:
            status = error.code
            context.status = status
            context.view_name = status2name[status]
            context.view = root.get_view(context.view_name)
            if server.auth_type == 'http_basic':
                basic_header = 'Basic realm="%s"' % server.auth_realm
                response.set_header('WWW-Authenticate', basic_header)
        except ClientError, error:
            status = error.code
            context.status = status
            context.view_name = status2name[status]
            context.view = root.get_view(context.view_name)
        else:
            # Everything goes fine so far
            context.status = 200

        # (2) Always deserialize the query
        resource = context.resource
        view = context.view
        try:
            context.query = view.get_query(context)
        except FormError, error:
            method = view.on_query_error
            context.query_error = error
        except:
            cls.internal_server_error(server, context)
            method = None
        else:
            method = view.POST

        # (3) Render
        if method is not None:
            try:
                context.entity = method(resource, context)
            except:
                cls.internal_server_error(server, context)
            else:
                # Ok: set status
                if isinstance(context.entity, Reference):
                    context.status = 302

        # (4) Commit the transaction commit
        if context.status < 400:
            cls.commit_transaction(server, context)
        else:
            server.abort_transaction(context)

        # (5) Build response, when postponed (useful for POST methods)
        if isinstance(context.entity, (FunctionType, MethodType)):
            try:
                context.entity = context.entity(context.resource, context)
            except:
                cls.internal_server_error(server, context)
            server.abort_transaction(context)

        # (6) After Traverse hook
        try:
            context.site_root.after_traverse(context)
        except:
            cls.internal_server_error(server, context)

        # (7) Build and return the response
        context.response.set_status(context.status)
        cls.set_body(server, context)

        # (8) Ok
        return context.response



###########################################################################
# Registry
###########################################################################

methods = {}


def register_method(method, method_handler):
    methods[method] = method_handler


register_method('GET', GET)
register_method('HEAD', HEAD)
register_method('POST', POST)

