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
from itools.core import local_tz
from itools.log import log_error
from itools.uri import Reference

# Local imports
from exceptions import ClientError, NotModified, Forbidden, NotFound
from exceptions import Unauthorized, FormError



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



class RequestMethod(object):


    @classmethod
    def check_access(cls, context):
        """Tell whether the user is allowed to access the view
        """
        # Get the check-point
        if context.view.is_access_allowed(context):
            return

        # Unauthorized (401)
        if context.user is None:
            raise Unauthorized

        # Forbidden (403)
        raise Forbidden



    @classmethod
    def check_cache(cls, context):
        """Implement cache if your method supports it.
        Most methods don't, hence the default implementation.
        """
        if context.method == 'GET':
            # 1. Get the view's modification time
            mtime = context.view.get_mtime(context)
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
        """Return True if your method is supposed to change the state.
        """
        if context.method in ('POST', 'PUT'):
            return True
        return getattr(context, 'commit', True) and context.status < 400


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
    def handle_request(cls, context):
        root = context.site_root
        server = context.server
        content_type = context.get_header('content-type')
        if content_type:
            content_type, type_parameters = content_type
        is_json_request = content_type == 'application/json'

        # (1) Find out the requested view
        try:
            response = server.dispatcher.resolve(str(context.path))
            if response:
                # Find a match in the dispatcher
                view, query = response
                params = {'context': context, 'query': query}
                context.resource = root
                context.view = view
            else:
                # The requested resource and view
                cls.find_resource(context)
                cls.find_view(context)
                params = {'context': context, 'resource': context.resource}
            # Access Control
            cls.check_access(context)
            # Check the request method is supported
            context.view_method = getattr(context.view, context.method, None)
            # Check the client's cache
            cls.check_cache(context)
        except ClientError, error:
            status = error.code
            context.status = status
            if is_json_request or context.agent_is_a_robot():
                kw = {'status': status, 'error': error.title}
                context.return_json(kw)
                context.set_response_from_context()
                return
            else:
                context.resource = root
                params = {'context': context, 'resource': context.resource}
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
            method = getattr(view, context.method)

        # (3) Render
        if method is not None:
            try:
                context.entity = method(**params)
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
                context.entity = context.entity(**params)
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

        # Cookies for authentification
        if context.user and context.server.session_timeout != timedelta(0):
            cookie = context.get_cookie('iauth')
            context._set_auth_cookie(cookie)

        # (7) Build and return the response
        context.set_response_from_context()


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



    @classmethod
    def internal_server_error(cls, context):
        log_error('Internal Server Error', domain='itools.web')
        context.status = 500
        context.entity = context.root.internal_server_error(context)


