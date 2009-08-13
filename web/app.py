# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from urllib import unquote

# Import from itools
from itools.handlers import BaseDatabase
from itools.http import Application, UNAUTHORIZED, FORBIDDEN, NOT_FOUND



class WebApplication(Application):

    database = BaseDatabase()

    #######################################################################
    # Resource
    #######################################################################
    def find_resource(self, context):
        """Sets 'context.resource' to the requested resource if it exists.

        Otherwise sets 'context.status' to 404 (not found error) and
        'context.resource' to the latest resource in the path that does exist.
        """
        # Split the path so '/a/b/c/;view' becomes ('/a/b/c', 'view')
        name = context.path.get_name()
        if name and name[0] == ';':
            path = context.path[:-1]
            view = name[1:]
        else:
            path = context.path
            view = None

        # Get the resource
        resource = self.get_resource(path, soft=True)
        if resource is None:
            return NOT_FOUND
        context.resource = resource

        # Get the view
        context.view = resource.get_view(view, context.query)
        if context.view is None:
            return NOT_FOUND


    #######################################################################
    # Authorization
    #######################################################################
    def get_credentials(self, context):
        # Credentials
        cookie = context.get_cookie('__ac')
        if cookie is None:
            return None

        cookie = unquote(cookie)
        cookie = decodestring(cookie)
        username, password = cookie.split(':', 1)
        if username is None or password is None:
            return None

        return username, password


    def check_access(self, context):
        # Access Control
        resource = context.resource
        ac = resource.get_access_control()
        if not ac.is_access_allowed(context, resource, context.view):
            return FORBIDDEN if context.user else UNAUTHORIZED


    #######################################################################
    # Authorization
    #######################################################################
    def get_allowed_methods(self, context):
        if context.view is None:
            return HTTPApplication.get_allowed_methods(self, context)

        view = context.view
        methods = [
            x for x in self.known_methods
            if getattr(view, self.known_methods[x], None) ]
        methods = set(methods)
        methods.add('OPTIONS')
        return methods

