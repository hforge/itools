# -*- coding: UTF-8 -*-
# Copyright (C) 2017 Alexandre Bonny <alexandre.bonny@protonmail.com>
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
from itools.web import BaseView, WebServer, Context
from itools.web.static import StaticView


class View(BaseView):

    def GET(self, kw):
        return 'Welcome ' + kw.get('name')



class Root(object):

    context_cls = Context

    def before_traverse(self, context):
        pass

SERVER = None

class RouterTestCase(TestCase):

    def setUp(self):
        global SERVER
        # Init context
        self.context = Context(root=Root())
        if SERVER is None:
            SERVER = WebServer(root=Root())
            SERVER.listen('127.0.0.1', 8080)


    def test_dispatch_router(self):
        global SERVER
        SERVER.dispatcher.add_route('/rest/welcome/{name}', View)
        # Check good request
        response = SERVER.do_request(method='GET',
                                     path='/rest/welcome/test',
                                     context=self.context())
        assert response.get('status') == 200
        assert response.get('entity') == 'Welcome test'
        # Check bad request
        response = SERVER.do_request(method='GET',
                                     path='/rest/welcome1/test',
                                     context=self.context())
        assert response.get('status') == 404


    def test_static_router(self):
        global SERVER
        SERVER.dispatcher.add_route('/ui/{name:any}', StaticView)
        # Launch server
        response = SERVER.do_request(method='GET',
                                     path='/static/hello.txt',
                                     context=self.context(mount_path='/static/'))
        assert response.get('entity') == 'hello world\n'



if __name__ == '__main__':
    main()
