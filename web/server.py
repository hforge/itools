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
from os import fstat, getpid, remove as remove_file
from time import strftime
from traceback import format_exc
from urllib import unquote
from warnings import warn
from sys import exc_info

# Import from itools
from itools.handlers import BaseDatabase
from itools.http import HTTPServer, get_response
from itools.http import ClientError, NotModified, BadRequest, Forbidden
from itools.http import NotFound, Unauthorized, NotImplemented
from itools.http import MethodNotAllowed
from itools.i18n import init_language_selector
from itools.log import WARNING, register_logger, log_error, log_warning
from itools.uri import Reference
from context import Context, set_context, select_language
from context import FormError
from views import BaseView



def web_logger(domain, level, message, filepath, min_level):
    # Log only if mimimum level reached
    if level < min_level:
        return

    # Build message
    now = strftime('%Y-%m-%d %H:%M:%S')
    message = '{0} - {1} - {2}\n'.format(now, domain, message)

    # Case 1: Standard error
    if filepath is None:
        stderr.write(message)
        stderr.flush()
        return

    # Case 2: File
    with open(filepath, 'a') as f:
        f.write(message)
        f.flush()



class WebServer(HTTPServer):

    access_log = None
    event_log = None

    database = BaseDatabase()


    def __init__(self, root, address='', port=8080, access_log=None,
                 event_log=None, log_level=WARNING, pid_file=None,
                 auth_type='cookie', auth_realm='Restricted Area'):

        HTTPServer.__init__(self, address, port)

        # The application's root
        self.root = root
        # Access log
        if access_log is not None:
            self.access_log_path = access_log
            self.access_log = open(access_log, 'a+')

        # Events log: build handler
        register_logger(None, web_logger, event_log, log_level)

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

        try:
            HTTPServer.start(self)
        finally:
            # Close files
            if self.access_log is not None:
                self.access_log.close()
            if self.event_log is not None:
                self.event_log.close()
            # Remove pid file
            if self.pid_file is not None:
                remove_file(self.pid_file)


    ########################################################################
    # Logging
    ########################################################################
    def _log_access(self, line):
        log = self.access_log
        if log is None:
            return

        # Check the file has not been removed
        if fstat(log.fileno())[3] == 0:
            log = open(self.access_log_path, 'a+')
            self.access_log = log

        # Write
        log.write(line)
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
        log_error(summary + details)


    def log_warning(self, context=None):
        exc_type, exc_value, traceback = exc_info()
        log_warning("%s: %s" % (exc_type.__name__, exc_value))


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
    def http_get(self, request):
        return GET.handle_request(self, request)


    def http_post(self, request):
        return POST.handle_request(self, request)


    def http_put(self, request):
        from webdav import PUT
        return PUT.handle_request(self, request)


    def http_delete(self, request):
        return DELETE.handle_request(self, request)


    def http_lock(self, request):
        from webdav import LOCK
        return LOCK.handle_request(self, request)


    def http_unlock(self, request):
        from webdav import UNLOCK
        return UNLOCK.handle_request(self, request)


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
    def handle_request(cls, server, request):
        # Make the context
        context = Context(request)
        server.init_context(context)

        # (1) Find out the requested resource and view
        response = context.response
        root = context.site_root
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
