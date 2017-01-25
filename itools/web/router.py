# -*- coding: UTF-8 -*-
# Copyright (C) 2016 Taverne Sylvain <taverne.sylvain@gmail.com>
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
from copy import copy
from datetime import timedelta
from sys import exc_clear
from types import FunctionType, MethodType

# Import from itools
from itools.core import prototype, local_tz
from itools.log import log_error
from itools.uri import Reference

# Local imports
from exceptions import ClientError, NotModified, Forbidden, NotFound, Conflict
from exceptions import NotImplemented, MethodNotAllowed, Unauthorized
from exceptions import FormError
from views import BaseView



###########################################################################
# The Request Methods
###########################################################################
status2name = {
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    405: 'method_not_allowed',
    409: 'conflict',
}


def find_view_by_method(context):
    """Associating an uncommon HTTP or WebDAV method to a special view.
    method "PUT" -> view "http_put" <instance of BaseView>
    """
    method_name = context.method
    view_name = "http_%s" % method_name.lower()
    context.view = context.resource.get_view(view_name)
    if context.view is None:
        raise NotImplemented, 'method "%s" is not implemented' % method_name



class RequestMethod(object):

    pass



class BaseDatabaseRequestMethod(RequestMethod):

    @classmethod
    def commit_transaction(cls, context):
        database = context.database
        # Check conditions are met
        if cls.check_transaction(context) is False:
            database.abort_changes()
            return

        # Save changes
        try:
            database.save_changes()
        except Exception:
            cls.internal_server_error(context)


    @classmethod
    def check_transaction(cls, context):
        return False


    @classmethod
    def set_body(cls, context):
        context.set_response_from_context()



    @classmethod
    def internal_server_error(cls, context):
        log_error('Internal Server Error', domain='itools.web')
        context.status = 500
        context.entity = context.root.internal_server_error(context)




class DatabaseRequestMethod(BaseDatabaseRequestMethod):

    @classmethod
    def find_resource(cls, context):
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
    def find_view(cls, context):
        query = context.uri.query
        context.view = context.resource.get_view(context.view_name, query)
        if context.view is None:
            raise NotFound


    @classmethod
    def check_access(cls, context):
        """Tell whether the user is allowed to access the view on the
        resource.
        """
        # Get the check-point
        if context.is_access_allowed(context.resource, context.view):
            return

        # Unauthorized (401)
        if context.user is None:
            raise Unauthorized

        # Forbidden (403)
        raise Forbidden


    @classmethod
    def check_method(cls, context, method_name=None):
        if method_name is None:
            method_name = context.method
        # Get the method
        view = context.view
        method = getattr(view, method_name, None)
        if method is None:
            message = '%s has no "%s" method' % (view, method_name)
            raise NotImplemented, message
        context.view_method = method


    @classmethod
    def check_cache(cls, context):
        """Implement cache if your method supports it.
        Most methods don't, hence the default implementation.
        """


    @classmethod
    def check_conditions(cls, context):
        """Check conditions to match before the response can be processed:
        resource, state, request headers...
        """


    @classmethod
    def check_transaction(cls, context):
        """Return True if your method is supposed to change the state.
        """
        return getattr(context, 'commit', True) and context.status < 400



    @classmethod
    def handle_request(cls, context):
        root = context.site_root

        # (1) Find out the requested resource and view
        try:
            # The requested resource and view
            cls.find_resource(context)
            cls.find_view(context)
            # Access Control
            cls.check_access(context)
            # Check the request method is supported
            cls.check_method(context)
            # Check the client's cache
            cls.check_cache(context)
            # Check pre-conditions
            cls.check_conditions(context)
        except ClientError, error:
            status = error.code
            context.status = status
            if context.agent_is_a_robot():
                context.entity = error.title
                context.set_content_type('text/plain')
                context.set_response_from_context()
                return
            context.view_name = status2name[status]
            context.view = root.get_view(context.view_name)
        except NotModified:
            context.http_not_modified()
            return
        finally:
            # Fucking Python. Clear the exception, otherwise a later call
            # to the logging system will print an exception that has been
            # handled already.
            exc_clear()

        # (2) Always deserialize the query
        resource = context.resource
        view = context.view
        try:
            context.query = view.get_query(context)
        except FormError, error:
            # If the query is invalid we consider that URL do not exist.
            # Otherwise anybody can create many empty webpages,
            # which is very bad for SEO.
            context.status = 404
            context.form_error = error
            method = view.on_query_error
        except Exception:
            cls.internal_server_error(context)
            method = None
        else:
            # GET, POST...
            method = getattr(view, cls.method_name)

        # (3) Render
        if method is not None:
            try:
                context.entity = method(resource, context)
            except Exception:
                cls.internal_server_error(context)
            else:
                # Ok: set status
                cls.set_status_from_entity(context)

        # (4) Commit the transaction
        cls.commit_transaction(context)

        # (5) Build response, when postponed (useful for POST methods)
        if isinstance(context.entity, (FunctionType, MethodType)):
            context.status = None
            try:
                context.entity = context.entity(context.resource, context)
            except Exception:
                cls.internal_server_error(context)
            else:
                cls.set_status_from_entity(context)
            context.database.abort_changes()

        # (6) After Traverse hook
        try:
            context.site_root.after_traverse(context)
        except Exception:
            cls.internal_server_error(context)
            context.set_content_type('text/html', charset='UTF-8')

        # (7) Build and return the response
        cls.set_body(context)


    @classmethod
    def set_status_from_entity(cls, context):
        if context.status is not None:
            pass
        elif isinstance(context.entity, Reference):
            context.status = 302
        elif context.entity is None:
            context.status = 204
        else:
            context.status = 200



class SafeMethod(DatabaseRequestMethod):

    @classmethod
    def check_transaction(cls, context):
        return False


class GET(SafeMethod):

    method_name = 'GET'


    @classmethod
    def check_cache(cls, context):
        # 1. Get the resource's modification time
        resource = context.resource
        mtime = context.view.get_mtime(resource)
        if mtime is None:
            return
        mtime = mtime.replace(microsecond=0)
        # If naive, assume local time
        if mtime.tzinfo is None:
            mtime = local_tz.localize(mtime)

        # 2. Set Last-Modified
        context.mtime = mtime

        # 3. Check for If-Modified-Since
        if_modified_since = context.get_header('if-modified-since')
        if if_modified_since and if_modified_since >= mtime:
            context.set_header('Last-Modified', mtime)
            # Cache-Control: max-age=1
            # (because Apache does not cache pages with a query by default)
            context.set_header('Cache-Control', 'max-age=1')
            raise NotModified


    @classmethod
    def set_body(cls, context):
        super(GET, cls).set_body(context)
        if context.status != 200:
            return

        if context.mtime:
            context.set_header('Last-Modified', context.mtime)
            # Cache-Control: max-age=1
            # (because Apache does not cache pages with a query by default)
            context.set_header('Cache-Control', 'max-age=1')
        elif context.user and context.server.session_timeout != timedelta(0):
            cookie = context.get_cookie('iauth')
            context._set_auth_cookie(cookie)



class HEAD(GET):

    @classmethod
    def check_method(cls, context):
        GET.check_method(context, method_name='GET')



class POST(DatabaseRequestMethod):

    method_name = 'POST'


    @classmethod
    def check_method(cls, context):
        # If there was an error, the method name always will be 'GET'
        if context.status is None:
            method_name = 'POST'
        else:
            method_name = 'GET'
        DatabaseRequestMethod.check_method(context, method_name=method_name)



class OPTIONS(SafeMethod):

    @classmethod
    def handle_request(cls, context):
        root = context.site_root

        known_methods = ['GET', 'HEAD', 'POST', 'OPTIONS', 'PUT', 'DELETE']
        allowed = []

        # (1) Find out the requested resource and view
        try:
            cls.find_resource(context)
            cls.find_view(context)
        except ClientError, error:
            status = error.code
            context.status = status
            context.view_name = status2name[status]
            context.view = root.get_view(context.view_name)
        else:
            # (2b) Check methods supported by the view
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
            # DELETE is unsupported at the root
            if context.path == '/':
                allowed.remove('DELETE')

        # (3) Render
        context.entity = None
        context.status = 200

        # (5) After Traverse hook
        try:
            context.site_root.after_traverse(context)
        except Exception:
            cls.internal_server_error(context)

        # (6) Build and return the response
        cls.set_body(context)



class PUT(DatabaseRequestMethod):
    """The client must send a correct "If-Unmodified-Since" header to be
       authorized to PUT.
    """

    method_name = 'PUT'


    @classmethod
    def find_view(cls, context):
        # Look for the "put" view
        return find_view_by_method(context)


    @classmethod
    def check_conditions(cls, context):
        """The resource is not locked, the request must have a correct
           "If-Unmodified-Since" header.
        """
        if_unmodified_since = context.get_header('If-Unmodified-Since')
        if if_unmodified_since is None:
            raise Conflict
        mtime = context.resource.get_value('mtime').replace(microsecond=0)
        if mtime > if_unmodified_since:
            raise Conflict


    @classmethod
    def set_body(cls, context):
        super(PUT, cls).set_body(context)

        # Set the Last-Modified header (if possible)
        mtime = context.resource.get_value('mtime')
        if mtime is None:
            return
        mtime = mtime.replace(microsecond=0)
        context.set_header('Last-Modified', mtime)



class DELETE(RequestMethod):

    method_name = 'DELETE'


    @classmethod
    def find_view(cls, context):
        # Look for the "delete" view
        return find_view_by_method(context)


    @classmethod
    def check_conditions(cls, context):
        resource = context.resource
        parent = resource.parent
        # The root cannot delete itself
        if parent is None:
            raise MethodNotAllowed




class BaseRouter(prototype):

    def handle_request(self, method_name, context):
        request_method = self.methods[method_name]
        return request_method.handle_request(context)



class DatabaseRouter(BaseRouter):

    methods = {'GET': GET,
               'POST': POST,
               'PUT': PUT,
               'HEAD': HEAD,
               'OPTIONS': OPTIONS,
               'DELETE': DELETE}
