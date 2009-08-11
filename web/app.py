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
from copy import copy
from urllib import unquote

# Import from itools
from itools.handlers import BaseDatabase
from itools.http import Application, FOUND, NOT_FOUND



class WebApplication(Application):

    database = BaseDatabase()


    def __init__(self, root):
        self.root = root


    def find_host(self, context):
        """This method may be overriden to support virtual hosting.
        """
        context.host = self.root


    def find_resource(self, context):
        """Sets 'context.resource' to the requested resource if it exists.

        Otherwise sets 'context.status' to 404 (not found error) and
        'context.resource' to the latest resource in the path that does exist.
        """
        host = context.host
        path = copy(context.path)
        path.startswith_slash = False

        resource = host.get_resource(path, soft=True)
        if resource is None:
            return NOT_FOUND
        context.resource = resource
        return FOUND


    def find_user(self, context):
        # Credentials
        cookie = context.get_cookie('__ac')
        if cookie is None:
            return

        cookie = unquote(cookie)
        cookie = decodestring(cookie)
        username, password = cookie.split(':', 1)
        if username is None or password is None:
            return

        # Authentication
        user = self.root.find_user(username)
        if user is not None and user.authenticate(password):
            context.user = user

