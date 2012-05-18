# -*- coding: UTF-8 -*-
# Copyright (C) 2006, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
# along with this program; if not, write to the:
# Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA

# Import from itools
from itools.handlers import RWDatabase
from itools.loop import Loop
from itools.web import WebServer, RootResource, BaseView


class MyView(BaseView):
    access = True
    def GET(self, resource, context):
        context.set_content_type('text/plain')
        return 'Hello World'

class MyRoot(RootResource):
    default_view_name = 'my_view'
    my_view = MyView()

if __name__ == '__main__':
    root = MyRoot()
    server = WebServer(root)
    server.listen('localhost', 8080)
    server.database = RWDatabase()
    loop = Loop()
    loop.run()
