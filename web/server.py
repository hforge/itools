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
from logging import getLogger, WARNING, FileHandler, StreamHandler, Formatter
from os import fstat, getpid, remove as remove_file
from types import FunctionType, MethodType
from signal import signal, SIGINT
from socket import socket as Socket, error as SocketError
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from time import strftime
from traceback import format_exc
from urllib import unquote
from warnings import warn
from sys import exc_info

# Import from itools
from itools.handlers import BaseDatabase
from itools.http import Request, get_response
from itools.http import ClientError, NotModified, BadRequest, Forbidden
from itools.http import NotFound, Unauthorized, HTTPError, NotImplemented
from itools.http import MethodNotAllowed
from itools.i18n import init_language_selector
from itools.uri import Reference
from context import Context, set_context, select_language
from context import FormError
from views import BaseView

# Import from gobject
from gobject import MainLoop, io_add_watch, source_remove
from gobject import IO_IN, IO_OUT, IO_PRI, IO_ERR, IO_HUP

# Some constants
IO_READ = IO_IN | IO_PRI | IO_ERR | IO_HUP
IO_WRITE = IO_OUT | IO_ERR | IO_HUP

MAX_REQUESTS = 200 # Used to limit the load of the server


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
            # Send the data read so far
            raise EOFError, buffer
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


logger_data = getLogger('data')
logger_http = getLogger('http')
logger_loop = getLogger('loop')



class Server(object):

    access_log = None
    event_log = None

    database = BaseDatabase()


    def __init__(self, root, address=None, port=None, access_log=None,
                 event_log=None, log_level=WARNING, pid_file=None,
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

        # Events log: build handler
        if event_log is None:
            handler = StreamHandler()
        else:
            handler = FileHandler(event_log)
        formatter = Formatter('%(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        # Events log: set handler
        logger_data.addHandler(handler)
        logger_http.addHandler(handler)
        logger_loop.addHandler(handler)
        # Level
        logger_data.setLevel(log_level)
        logger_http.setLevel(log_level)
        logger_loop.setLevel(log_level)

        # The pid file
        self.pid_file = pid_file

        # Authentication options
        self.auth_type = auth_type
        self.auth_realm = auth_realm

        # The requests dict
        # mapping {<fileno>: (conn, id, + some useful informations) }
        self.requests = {}

        # The connection
        self.ear = None
        self.ear_fileno = 0
        self.ear_id = 0

        # Main Loop
        self.main_loop = MainLoop()


    def new_connection(self):
        """Registers the connection to read the new request.
        """
        # Get the connection and client address
        try:
            conn, client_address = self.ear.accept()
        except SocketError:
            return

        # Debug
        peer = conn.getpeername()
        logger_loop.debug('%s:%s => New connection' % peer)

        # Set non-blocking mode
        conn.setblocking(0)
        # Register the connection
        fileno = conn.fileno()
        id = io_add_watch(fileno, IO_READ, self.events_callback)
        # Build and store the request
        request = Request()
        wrapper = SocketWrapper(conn)
        loader = request.non_blocking_load(wrapper)
        self.requests[fileno] = conn, id, request, loader


    def load_request(self, fileno):
        """Loads the request, and when it is done, handles it.
        """
        requests = self.requests

        # Load request
        conn, id, request, loader = requests.pop(fileno)
        source_remove(id)

        # Debug
        peer = conn.getpeername()
        logger_loop.debug('%s:%s => IN' % peer)

        try:
            # Read
            loader.next()
        except StopIteration:
            # We are done
            try:
                response = self.handle_request(request)
            except:
                # This should never happen
                conn.close()
                return
        except BadRequest:
            # Error loading
            response = get_response(400)
            self.log_error()
        except:
            # Unexpected error
            # FIXME Send a response to the client (BadRequest, etc.)?
            self.log_error()
            conn.close()
            return
        else:
            # Not finished
            id = io_add_watch(fileno, IO_READ, self.events_callback)
            requests[fileno] = conn, id, request, loader
            return

        # We have a response to send
        # Log access
        self.log_access(conn, request, response)
        # We do not support persistent connections yet
        response.set_header('connection', 'close')
        # Ready to send response
        response = response.to_str()
        id = io_add_watch(fileno, IO_WRITE, self.events_callback)
        requests[fileno] = conn, id, response


    def send_response(self, fileno):
        requests = self.requests

        conn, id, response = requests.pop(fileno)
        source_remove(id)

        # Debug
        peer = conn.getpeername()
        logger_loop.debug('%s:%s => OUT' % peer)

        # Send the response
        try:
            n = conn.send(response)
        except SocketError:
            conn.close()
        else:
            response = response[n:]
            if response:
                id = io_add_watch(fileno, IO_WRITE, self.events_callback)
                requests[fileno] = conn, id, response
            else:
                conn.close()


    def events_callback(self, fileno, event):
        requests = self.requests

        try:
            if event & IO_IN or event & IO_PRI:
                if fileno == self.ear_fileno:
                    self.new_connection()
                else:
                    self.load_request(fileno)
            elif event & IO_OUT:
                self.send_response(fileno)
            elif event & IO_ERR or event & IO_HUP:
                if event == IO_ERR:
                    logger_loop.debug('ERROR CONDITION')
                else:
                    logger_loop.debug('HUNG UP')

                conn, id = requests.pop(fileno)[:2]
                source_remove(id)
        except:
            self.log_error()

        # The end ??
        if not requests:
            self.stop()

        return True


    def stop_gracefully(self, signum, frame):
        requests = self.requests
        ear_fileno = self.ear_fileno

        if ear_fileno not in requests:
            return

        source_remove(self.ear_id)
        self.ear.close()
        del requests[ear_fileno]
        print 'Shutting down the server (gracefully)...'

        # Yet the end ?
        if not requests:
            self.stop()


    def start(self):
        # Language negotiation
        init_language_selector(select_language)

        # PID file
        if self.pid_file is not None:
            pid = getpid()
            open(self.pid_file, 'w').write(str(pid))

        # Set up the connection
        ear = self.ear = Socket(AF_INET, SOCK_STREAM)
        # Allow to reuse the address, this solves the bug "icms.py won't
        # close its connection properly". But is probably not the right
        # solution (FIXME).
        ear.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        ear.bind((self.address, self.port))
        ear.listen(5)
        ear_fileno = self.ear_fileno = ear.fileno()
        ear_id = self.ear_id = io_add_watch(ear_fileno, IO_READ,
                                            self.events_callback)
        self.requests[ear_fileno] = ear, ear_id

        # Set up the graceful stop
        signal(SIGINT, self.stop_gracefully)

        # Main loop !!
        self.main_loop.run()

        # Close files
        if self.access_log is not None:
            self.access_log.close()
        if self.event_log is not None:
            self.event_log.close()
        # Remove pid file
        if self.pid_file is not None:
            remove_file(self.pid_file)


    def stop(self):
        self.main_loop.quit()


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
        host = request.get_remote_ip()
        if host is None:
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
        if context is None:
            summary = ''
            details = ''
        else:
            # The summary
            user = context.user
            if user is None:
                summary = '%s\n' % context.uri
            else:
                summary = '%s (user: %s)\n' % (context.uri, user.name)
            # Details, the headers
            request = context.request
            details = (
                request.request_line_to_str()
                + request.headers_to_str()
                + '\n')

        # The traceback
        details = details + format_exc()

        # Indent the details
        lines = [ ('  %s\n' % x) for x in details.splitlines() ]
        details = ''.join(lines)

        # Log
        logger_http.error(summary + details)


    def log_warning(self, context=None):
        exc_type, exc_value, traceback = exc_info()
        logger_http.warning("%s: %s" % (exc_type.__name__, exc_value))


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
        # 503 Service Unavailable
        if len(self.requests) > MAX_REQUESTS:
            return get_response(503)

        # 501 Not Implemented
        method_name = request.method
        method = methods.get(method_name)
        if method is None:
            return get_response(501)

        # Make the context
        context = Context(request)
        self.init_context(context)

        # Handle request
        try:
            method.handle_request(self, context)
        except HTTPError, exception:
            self.log_error(context)
            return get_response(exception.code)
        except:
            self.log_error(context)
            return get_response(500)

        # Ok
        return context.response



###########################################################################
# The Request Methods
###########################################################################

status2name = {
    401: 'http_unauthorized',
    403: 'http_forbidden',
    404: 'http_not_found',
    405: 'http_method_not_allowed',
    409: 'http_conflict'}


def find_view_by_method(server, context):
    """Associating an uncommon HTTP or WebDAV method to a special view.
    method "PUT" -> view "http_put" <instance of BaseView>
    """
    method_name = context.request.method
    view_name = "http_%s" % method_name.lower()
    context.view = context.resource.get_view(view_name)
    if context.view is None:
        raise NotImplemented, 'method "%s" is not implemented' % method_name


class RequestMethod(object):

    @classmethod
    def find_resource(cls, server, context):
        """Sets 'context.resource' to the requested resource if it exists.

        Otherwise sets 'context.status' to 404 (not found error) and
        'context.resource' to the latest resource in the path that does exist.
        """
        # We start at the sire-root
        root = context.site_root
        path = copy(context.path)
        path.startswith_slash = False

        # Found
        resource = root.get_resource(path, soft=True)
        if resource is not None:
            context.resource = resource
            return

        # Not Found
        while resource is None:
            path = path[:-1]
            resource = root.get_resource(path, soft=True)
        context.resource = resource
        raise NotFound


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
    def check_method(cls, server, context, method_name=None):
        if method_name is None:
            method_name = context.request.method
        # Get the method
        view = context.view
        method = getattr(view, method_name, None)
        if method is None:
            message = '%s has no "%s" method' % (view, method_name)
            raise NotImplemented, message
        context.view_method = method


    @classmethod
    def check_cache(cls, server, context):
        """Implement cache if your method supports it.
        Most methods don't, hence the default implementation.
        """
        pass


    @classmethod
    def check_conditions(cls, server, context):
        """Check conditions to match before the response can be processed:
        resource, state, request headers...
        """
        pass


    @classmethod
    def check_transaction(cls, server, context):
        """Return True if your method is supposed to change the state.
        """
        raise NotImplementedError


    @classmethod
    def commit_transaction(cls, server, context):
        database = server.database
        # Check conditions are met
        if cls.check_transaction(server, context) is False:
            database.abort_changes()
            return

        # Save changes
        try:
            database.save_changes()
        except:
            cls.internal_server_error(server, context)


    @classmethod
    def set_body(cls, server, context):
        response = context.response
        body = context.entity
        if isinstance(body, Reference):
            reference = context.uri.resolve(body)
            response.redirect(reference, 302)
            return
        response.set_body(body)
        length = response.get_content_length()
        response.set_header('content-length', length)


    @classmethod
    def internal_server_error(cls, server, context):
        server.log_error(context)
        context.status = 500
        root = context.site_root
        context.entity = root.http_internal_server_error.GET(root, context)


    @classmethod
    def handle_request(cls, server, context):
        response = context.response
        root = context.site_root

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
            # Check pre-conditions
            cls.check_conditions(server, context)
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

        # (2) Always deserialize the query
        resource = context.resource
        view = context.view
        try:
            context.query = view.get_query(context)
        except FormError, error:
            context.method = view.on_query_error
            context.query_error = error
        except:
            cls.internal_server_error(server, context)
            context.method = None
        else:
            # GET, POST...
            context.method = getattr(view, cls.method_name)

        # (3) Render
        try:
            m = getattr(root.http_main, cls.method_name)
            context.entity = m(root, context)
        except:
            cls.internal_server_error(server, context)
        else:
            # Ok: set status
            if context.status is not None:
                pass
            elif isinstance(context.entity, Reference):
                context.status = 302
            elif context.entity is None:
                context.status = 204
            else:
                context.status = 200

        # (4) Commit the transaction
        cls.commit_transaction(server, context)

        # (5) Build and return the response
        response.set_status(context.status)
        cls.set_body(server, context)

        # (6) Ok
        return response



class GET(RequestMethod):

    method_name = 'GET'


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


    @classmethod
    def check_transaction(cls, server, context):
        # GET is not expected to change the state
        if getattr(context, 'commit', False) is True:
            # FIXME To be removed one day.
            warn("Use of 'context.commit' is strongly discouraged.")
            return True
        return False



class HEAD(GET):

    @classmethod
    def check_method(cls, server, context):
        GET.check_method(server, context, method_name='GET')


    @classmethod
    def set_body(cls, server, context):
        GET.set_body(server, context)
        # Drop the body from the response
        context.response.set_body(None)



class POST(RequestMethod):

    method_name = 'POST'


    @classmethod
    def check_method(cls, server, context):
        # If there was an error, the method name always will be 'GET'
        if context.status is None:
            method_name = 'POST'
        else:
            method_name = 'GET'
        RequestMethod.check_method(server, context, method_name=method_name)


    @classmethod
    def check_transaction(cls, server, context):
        return getattr(context, 'commit', True) and context.status < 400



class OPTIONS(RequestMethod):

    @classmethod
    def handle_request(cls, server, context):
        response = context.response
        root = context.site_root

        known_methods = methods.keys()

        # (1) Find out the requested resource and view
        if context.path == '*':
            # (1a) Server-registered methods
            allowed = known_methods
        else:
            allowed = []
            try:
                cls.find_resource(server, context)
                cls.find_view(server, context)
            except ClientError, error:
                status = error.code
                context.status = status
                context.view_name = status2name[status]
                context.view = root.get_view(context.view_name)
            else:
                # (1b) Check methods supported by the view
                resource = context.resource
                view = context.view
                for method_name in known_methods:
                    # Search on the resource's view
                    method = getattr(view, method_name, None)
                    if method is not None:
                        allowed.append(method_name)
                        continue
                    # Search on the resource itself
                    # PUT -> "put" view instance
                    view_name = "http_%s" % method_name.lower()
                    http_view = getattr(resource, view_name, None)
                    if isinstance(http_view, BaseView):
                        if getattr(http_view, method_name, None) is not None:
                            allowed.append(method_name)
                # OPTIONS is built-in
                allowed.append('OPTIONS')
                # TRACE is built-in
                allowed.append('TRACE')
                # DELETE is unsupported at the root
                if context.path == '/':
                    allowed.remove('DELETE')

        # (2) Render
        response.set_header('allow', ','.join(allowed))
        context.entity = None
        context.status = 200

        # (3) Build and return the response
        response.set_status(context.status)
        cls.set_body(server, context)

        # Ok
        return response



class TRACE(RequestMethod):

    @classmethod
    def handle_request(cls, server, context):
        request = context.request
        context.entity = request.to_str()
        cls.set_body(server, context)
        response = context.response
        response.set_header('content-type', 'message/http')
        response.set_status(200)
        return response



class DELETE(RequestMethod):

    method_name = 'DELETE'


    @classmethod
    def find_view(cls, server, context):
        # Look for the "delete" view
        return find_view_by_method(server, context)


    @classmethod
    def check_conditions(cls, server, context):
        resource = context.resource
        parent = resource.parent
        # The root cannot delete itself
        if parent is None:
            raise MethodNotAllowed


    @classmethod
    def check_transaction(cls, server, context):
        return getattr(context, 'commit', True) and context.status < 400



###########################################################################
# Registry
###########################################################################

methods = {}


def register_method(method, method_handler):
    methods[method] = method_handler


register_method('GET', GET)
register_method('HEAD', HEAD)
register_method('POST', POST)
register_method('OPTIONS', OPTIONS)
register_method('TRACE', TRACE)
register_method('DELETE', DELETE)
