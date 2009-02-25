# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from unittest import TestCase, main

# Import from itools
from itools import vfs
from itools.web import BaseView, RootResource, Server


class MyRootView(BaseView):
    access = True
    def GET(self, resource, context):
        return 'hello world'


class MyRoot(RootResource):
    default_view_name = 'view'
    view = MyRootView()


class ServerTestCase(TestCase):

    def test00_simple(self):
        root = MyRoot()
        server = Server(root)
##        server.start()




if __name__ == '__main__':
    main()
