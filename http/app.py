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


# These are the values that 'Application.find_resource' may return
MOVED = 301
REDIRECT = 307 # 302 in HTTP 1.0
UNAUTHORIZED = 401
FORBIDDEN = 403
NOT_FOUND = 404
GONE = 410 # Not available in HTTP 1.0


class HTTPResource(object):
    """This class is the base class for any HTTP resource.
    """



class Root(HTTPResource):
    """This is a demonstration class, used only as an example.
    """

    def http_get(self, context):
        context.set_status(200)
        context.set_body('text/plain', "Hello, I'am itools.http")



class Application(object):
    """This is at the same time the base class for every Web application,
    and a demo class that says "hello".
    """

    def find_host(self, context):
        pass


    def find_resource(self, context):
        if context.path == '/':
            context.resource = Root()
            return

        return NOT_FOUND


    def get_user(self, context):
        return None


    def check_access(self, context):
        pass


    known_methods = {
        'OPTIONS': 'http_options',
        'GET': 'http_get',
        'HEAD': 'http_get',
        'POST': 'http_post'}


    def get_allowed_methods(self, context):
        resource = context.resource
        methods = [
            x for x in self.known_methods
            if getattr(resource, self.known_methods[x], None) ]
        methods = set(methods)
        methods.add('OPTIONS')
        return methods


    def http_options(self, context):
        methods = self.get_allowed_methods(context.resource)
        context.set_status(200)
        context.set_header('Allow', ','.join(methods))


    def http_get(self, context):
        resource = context.resource
        resource.http_get(context)


    def http_post(self, context):
        resource = context.resource
        resource.http_post(context)

