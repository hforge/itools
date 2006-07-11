# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import sys
import time
import traceback
from urllib import unquote

# Import from itools
from itools import uri
##from itools.resources.socket import File
from itools.handlers.transactions import get_transaction
from itools.http.exceptions import (Forbidden, HTTPError, NotFound,
                                    Unauthorized)
from itools.http.request import Request
from itools.http.response import Response
from context import Context, get_context, set_context



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
                            loader = request.non_blocking_load(conn.recv)
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
            except:
                self.log_error()


    ########################################################################
    # Handle a request
    ########################################################################
    def GET(self, context):
        request, response = context.request, context.response
        # This is a safe method
        context.commit = False
        # Our canonical URLs never end with an slash
        if request.uri.path.endswith_slash:
            goto = copy(context.uri)
            goto.path.endswith_slash = False
            return 302, goto
        # Traverse
        status, method = self.traverse(context)
        if status == 200:
            # Check modification time
            mtime = getattr(object, '%s__mtime__' % context.method, None)
            if mtime is not None:
                mtime = mtime().replace(microsecond=0)
                response.set_header('last-modified', mtime)
                if request.method == 'GET':
                    if request.has_header('if-modified-since'):
                        msince = request.get_header('if-modified-since')
                        if mtime <= msince:
                            return 304, None
        # Call the method
        body = method(context) 
        if isinstance(body, str):
            # Post-process (used to wrap the body in a skin)
            body = context.root.after_traverse(context, body)
        elif isinstance(body, uri.Reference):
            # Redirection
            status = 302
        elif body is not None:
            # What?
            raise TypeError, 'unexpected value of type "%s"' % type(body)

        # Commit
        self.commit_transaction(context)

        return status, body


    def HEAD(self, context):
        if context.method == 'HEAD':
            context.method = 'GET'
        response = self.GET(context)
        content_length = response.get_content_length()
        response.set_header('content-length', content_length)
        response.set_body(None)
        return response


    def POST(self, context):
        request, response = context.request, context.response
        # Not a safe method
        context.commit = True
        # Traverse
        status, method = self.traverse(context)
        # Call the method
        body = method(context) 
        if isinstance(body, str):
            # Post-process (used to wrap the body in a skin)
            body = root.after_traverse(context, body)
        elif isinstance(body, uri.Reference):
            # Redirection
            status = 302
        elif body is not None:
            # What?
            raise TypeError, 'unexpected value of type "%s"' % type(body)

        # Commit
        self.commit_transaction(context)
 
        return status, body


    def PUT(self, context):
        context.commit = True
        return 501, None


    def LOCK(self, context):
        context.commit = True
        return 501, None


    def UNLOCK(self, context):
        context.commit = True
        return 501, None


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
            status = 500
            body = self.root.internal_server_error(context)

        # Set body
        if isinstance(body, str):
            response.set_body(body)
        elif isinstance(body, uri.Reference):
            context.redirect(body)

        # Set status
        response.set_status(status)
 
        # Check for errors
        if status >= 400:
            # Rollback transaction
            get_transaction().rollback()
            self.log_error(context)

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
        try:
            handler = context.handler = root.get_handler(context.path)
        except LookupError:
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
        # Get the transaction
        transaction = get_transaction()
        # Nothing to do
        if not transaction:
            return

        # Abort transaction if safe method, or if explicitly stated
        if context.commit is False:
            transaction.rollback()
            return

        # Before commit (hook)
        self.before_commit(transaction)

        # Transaction metadata
        user = context.user
        username = user and user.name or 'NONE'
        note = str(context.request.uri.path)

        # Start commit (hook)
        self.start_commit()

        try:
            transaction.commit(username, note)
        except:
            # Abort transaction
            transaction.rollback()
            # End commit, error (hook)
            self.end_commit_on_error()
            # Forward error
            raise

        # End commit, success (hook)
        self.end_commit_on_success()


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
        log = self.error_log
        if log is not None:
            log.write('\n')
            log.write('%s\n' % ('*' * 78))
            # The request data
            if context is not None:
                # The request
                request = context.request
                log.write(request.request_line_to_str())
                log.write(request.headers_to_str())
                # Other information
                user = context.user
                log.write('\n')
                log.write('URI     : %s\n' % str(context.uri))
                log.write('USER    : %s\n' % (user and user.name or None))

            # The traceback
            log.write('\n')
            traceback.print_exc(file=log)
            log.flush()


    ########################################################################
    # Hooks (to be overriden)
    ########################################################################
    def before_commit(self, transaction):
        pass


    def start_commit(self):
        pass


    def end_commit_on_success(self):
        get_transaction().clear()


    def end_commit_on_error(self):
        pass
