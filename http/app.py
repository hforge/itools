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



class HTTPResource(object):
    """This class is the base class for any HTTP resource.
    """

    def _get_resource_methods(self):
        return [ x[5:].upper() for x in dir(self) if x[:5] == 'http_' ]



class Root(HTTPResource):
    """This is a demonstration class, used only as an example.
    """

    def http_get(self, message):
        message.set_status(200)
        message.set_body('text/plain', "Hello, I'am itools.http")



class Application(object):
    """This is at the same time the base class for every Web application,
    and a demo class that says "hello".
    """

    def get_host(self, message):
        pass


    def get_resource(self, message):
        if message.path == '/':
            return Root()

        return None

