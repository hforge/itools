# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from base64 import decodestring
from copy import copy
from datetime import datetime
import os
import select
from select import POLLIN, POLLPRI, POLLOUT, POLLERR, POLLHUP, POLLNVAL
import socket
import time
import traceback
from urllib import unquote

# Import from itools
from itools.resources.socket import File
from itools.handlers.transactions import get_transaction
from itools.http.request import Request
from itools.http.response import Response
from itools.http.exceptions import BadRequest
from itools.web.exceptions import Forbidden, UserError
from itools.web.context import Context, get_context, set_context


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
        buffer = self.buffer
        # Check if there is already a line in the buffer
        if '\r\n' in buffer:
            line, self.buffer = buffer.split('\r\n', 1)
            return line
        # Read as much as possible
        recv = self.socket.recv
        while True:
            try:
                data = recv(512)
            except:
                return None
            buffer += data
            # Hit
            if '\r\n' in buffer:
                line, self.buffer = buffer.split('\r\n', 1)
                return line
            # Miss
            if len(data) < 512:
                self.buffer = buffer
                return None 



class Server(object):

    def __init__(self, root, address=None, port=None, access_log=None,
                 error_log=None, pid_file=None):
        if address is None:
            address = ''
        if port is None:
            port = 8080
        # The application's root
        self.root = root
        # The address and port the server will listen to
        self.address = address
        self.port = port
        # The access and error logs
        if access_log is not None:
            access_log = open(access_log, 'a+')
        if error_log is not None:
            error_log = open(error_log, 'a+')
        self.access_log = access_log
        self.error_log = error_log
        # The pid file
        self.pid_file = pid_file


    def start(self):
        if self.pid_file is not None:
            pid = os.getpid()
            open(self.pid_file, 'w').write(str(pid))

        ear = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow to reuse the address, this solves bug #199 ("icms.py won't
        # close its connection properly"), but is probably not the right
        # solution (XXX).
        ear.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ear.bind((self.address, self.port))
        ear.listen(5)
        ear_fileno = ear.fileno()

        # Mapping {<fileno>: (request, loader)}
        requests = {}
        # Set-up polling object
        POLL_READ = POLLIN | POLLPRI | POLLERR | POLLHUP | POLLNVAL
        POLL_WRITE = POLLOUT | POLLERR | POLLHUP | POLLNVAL
        poll = select.poll()
        poll.register(ear_fileno, POLL_READ)
        while True:
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
                            except KeyboardInterrupt:
                                raise
                            except:
                                self.log_error()
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
                        # XXX What to do here?
                        pass
                    elif event & POLLHUP:
                        # XXX What to do here?
                        pass
                    elif event & POLLNVAL:
                        # XXX What to do here?
                        pass
            except KeyboardInterrupt:
                ear.close()
                if self.access_log is not None:
                    self.access_log.close()
                if self.error_log is not None:
                    self.error_log.close()
                break
            except:
                self.log_error()


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
                         request.state.request_line, response.state.status,
                         response.get_content_length())
            log.write('%s - - [%s] "%s" %s %s\n' % namespace)
            log.flush()


    def log_error(self):
        log = self.error_log
        if log is not None:
            # The separator
            log.write('\n')
            log.write('%s\n' % ('*' * 78))
            # The date
            log.write('DATE: %s\n' % datetime.now())
            # The request data
            context = get_context()
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


    def before_commit(self, transaction):
        pass


    def start_commit(self):
        pass


    def end_commit_on_success(self):
        get_transaction().clear()


    def end_commit_on_error(self):
        pass


    def handle_request(self, request):
        # Build and set the context
        context = Context(request)
        context.server = self
        set_context(context)

        # Our canonical URLs never end with an slash
        if request.method == 'GET' and context.uri.path.endswith_slash:
            # Redirect to the same URL without the trailing slash
            goto = copy(context.uri)
            goto.path.endswith_slash = False
            response = Response(status_code=301)
            response.set_header('Location', goto)
            response.set_body('Moved Permanently')
            # Send response
            return response

        # Get the root handler
        root = self.root
        if root.is_outdated():
            root.load_state()
        context.root = root

        # Authenticate
        cname = '__ac'
        cookie = context.get_cookie(cname)
        if cookie is not None:
            cookie = unquote(cookie)
            cookie = decodestring(cookie)
            username, password = cookie.split(':', 1)
            try:
                user = root.get_handler('users/%s' % username)
            except LookupError:
                pass
            except:
                self.log_error()
            else:
                if user.authenticate(password):
                    context.user = user
        user = context.user

        # Hook (used to set the language)
        try:
            root.before_traverse()
        except:
            self.log_error()

        response = context.response
        # Traverse
        try:
            handler = root.get_handler(context.path)
        except LookupError:
            # Not Found (response code 404)
            response.set_status(404)
            method = root.not_found
            context.handler = root
        except:
            self.log_error()
            # Internal Server Error (500)
            response.set_status(500)
            method = root.internal_server_error
        else:
            context.handler = handler
            # Get the method name
            method_name = context.method
            if method_name is None:
                if request.method == 'HEAD':
                    method_name = 'GET'
                else:
                    method_name = request.method
            # Check the method exists
            try:
                getattr(handler, method_name)
            except AttributeError:
                # Not Found (response code 404)
                response.set_status(404)
                method = root.not_found
            else:
                # Get the method
                try:
                    method = handler.get_method(method_name)
                except:
                    self.log_error()
                    # Internal Server Error (500)
                    response.set_status(500)
                    method = root.internal_server_error
                else:
                    # Check security
                    if method is None:
                        if user is None:
                            # Unauthorized (401)
                            method = root.login_form
                        else:
                            # Forbidden (403)
                            method = root.forbidden
                    else:
                        mtime = getattr(handler, '%s__mtime__' % method_name, None)
                        if mtime is not None:
                            mtime = mtime().replace(microsecond=0)
                            response.set_header('last-modified', mtime)
                            if request.method == 'GET':
                                if request.has_header('if-modified-since'):
                                    msince = request.get_header('if-modified-since')
                                    if mtime <= msince:
                                        # Not modified (304)
                                        response.set_status(304)

        if response.get_status() != 304:
            # Set the list of needed resources. The method we are going to
            # call may need external resources to be rendered properly, for
            # example it could need an style sheet or a javascript file to
            # be included in the html head (which it can not control). This
            # attribute lets the interface to add those resources.
            context.styles = []
            context.scripts = []

            # Get the transaction object
            transaction = get_transaction()

            try:
                # Call the method
                if method.im_func.func_code.co_flags & 8:
                    response_body = method(**request.form)
                else:
                    response_body = method()
            except UserError, exception:
                # Redirection
                transaction.rollback()
                goto = copy(request.referrer)
                goto.query['message'] = exception.args[0].encode('utf8')
                context.redirect(goto)
                response_body = None
            except Forbidden:
                transaction.rollback()
                if user is None:
                    # Unauthorized (401)
                    response_body = root.login_form()
                else:
                    # Forbidden (403)
                    response_body = root.forbidden()
            except:
                self.log_error()
                transaction.rollback()
                response.set_status(500)
                response_body = root.internal_server_error()
            else:
                if transaction:
                    try:
                        self.before_commit(transaction)
                    except:
                        self.log_error()
                        transaction.rollback()
                        response.set_status(500)
                        response_body = root.internal_server_error()
                    else:
                        username = user and user.name or 'NONE'
                        note = str(request.uri.path)
                        # Save changes
                        self.start_commit()
                        try:
                            transaction.commit(username, note)
                        except:
                            self.log_error()
                            transaction.rollback()
                            self.end_commit_on_error()
                            response.set_status(500)
                            response_body = root.internal_server_error()
                        else:
                            self.end_commit_on_success()

            # Set the response body
            response.set_body(response_body)

            # After traverse hook
            try:
                root.after_traverse()
            except:
                response.set_status(500)
                body = root.internal_server_error()
                response.set_body(body)
                self.log_error()

        # HEAD
        if request.method == 'HEAD':
            content_length = response.get_content_length()
            response.set_header('content-length', content_length)
            response.set_body(None)

        # Finish, send back the response
        return response
