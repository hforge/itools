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
from select import select
import socket
import time
import traceback
from urllib import unquote

# Import from itools
from itools.resources.socket import File
from itools.handlers import transactions
from itools.web.exceptions import BadRequest, Forbidden, UserError
from itools.web.context import Context, get_context, set_context
from itools.web.request import Request
from itools.web.response import Response



class Server(object):

    def __init__(self, root, address='127.0.0.1', port=None, access_log=None,
                 error_log=None, pid_file=None):
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
        print 'Listen port %s' % self.port
        ear.listen(5)

        iwtd = [ear]
        owtd = []
        ewtd = []
        while True:
            try:
                iready, oready, eready = select(iwtd, owtd, ewtd)

                for x in iready:
                    if x is ear:
                        # New connection
                        try:
                            connection, client_address = ear.accept()
                        except socket.error:
                            continue

                        iwtd.append(connection)
                    else:
                        # Connection is ready
                        # XXX To further improve performance, the request
                        # object should be built as the information arrives,
                        # giving the control back to the main loop while
                        # waiting for new bytes. This probably means
                        # "load_state" should be a generator, what will
                        # require changes in the handlers design.
                        iwtd.remove(x)
                        self.handle_request(x)
            except KeyboardInterrupt:
                ear.close()
                if self.access_log is not None:
                    self.access_log.close()
                if self.error_log is not None:
                    self.error_log.close()
                break
            except:
                self.log_error()


    def log_access(self, connection, request_line, status, size):
        # Common Log Format
        #  - IP address of the client
        #  - RFC 1413 identity (not available)
        #  - username (XXX not provided right now should we?)
        #  - time (XXX we use the timezone name, while we should use the
        #    offset, e.g. +0100)
        #  - the request line
        #  - the status code
        #  - content length of the response
        if self.access_log is not None:
            host, port = connection.getpeername()
            now = time.strftime('%d/%b/%Y:%H:%M:%S %Z')
            self.access_log.write(
                '%s - - [%s] "%s" %s %s\n' % (host, now, request_line, status,
                                              size))


    def log_error(self):
        error_log = self.error_log
        error_log.write('\n')
        error_log.write('[Error]\n')
        error_log.write('date    : %s\n' % str(datetime.now()))

        # The request data
        context = get_context()
        if context is not None:
            request = context.request
            user = context.user
            error_log.write('uri     : %s\n' % str(context.uri))
            error_log.write('referrer: %s\n' % str(request.referrer))
            error_log.write('user    : %s\n' % (user and user.name or None))

        # The traceback
        error_log.write('\n')
        traceback.print_exc(file=error_log)
        error_log.flush()


    def after_commit(self):
        pass


    def handle_request(self, connection):
        # Build the request object
        resource = File(connection)
        try:
            request = Request(resource)
        except BadRequest, exception:
            request = None
            request_line = exception.args[0]
        except:
            self.log_error()
            request = None
            request_line = 'XXX'
        else:
            # Keep here (though redundant) to be used later in the access log
            request_line = request.state.request_line

        if request is None:
            # Build response for the 400 error
            response = Response(status_code=400)
            response.set_body('Bad Request')
            # Access Log
            content_length = response.get_content_length()
            self.log_access(connection, request_line, 400, content_length)
            # Send response
            response = response.to_str()
            connection.send(response)
            return

        # Build and set the context
        context = Context(request)
        set_context(context)

        # Get the root handler
        root = self.root
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
            transaction = transactions.get_transaction()

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
                    # Save changes
                    username = user and user.name or 'NONE'
                    note = str(request.path)
                    try:
                        transaction.commit(username, note)
                    except:
                        self.log_error()
                        transaction.rollback()
                        response.set_status(500)
                        response_body = root.internal_server_error()
                    else:
                        self.after_commit()

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

        # Access Log
        self.log_access(connection, request_line, response.state.status,
                        response.get_content_length())

        # HEAD
        if request.method == 'HEAD':
            content_length = response.get_content_length()
            response.set_header('content-length', content_length)
            response.set_body(None)

        # Finish, send back the response
        response = response.to_str()
        connection.send(response)
        connection.close()
