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
from itools.web import BaseView, WebServer, DispatchRouter, Context
from itools.web import StaticRouter

class View(BaseView):

    def GET(self, kw):
        return 'Welcome ' + kw.get('name')



class Root(object):
    context_cls = Context
    def before_traverse(self, context):
        pass

class RouterTestCase(TestCase):

    def setUp(self):
        # Init context and server
        self.context = Context(root=Root())
        self.server = WebServer(root=Root())


    def test_dispatch_router(self):
        self.rest_router = DispatchRouter()
        self.rest_router.add_route('/rest/welcome/{name}', View)
        self.server.set_router('/rest', self.rest_router)
        self.server.listen('127.0.0.1', 8080)
        response = self.server.do_request(method='GET',
                                     path='/rest/welcome/test',
                                     context=self.context(router=self.rest_router))
        assert response.get('status') == 200
        assert response.get('entity') == 'Welcome test'
        self.server.stop()


    """
    # TODO : Uncomment when stop server is working
    def test_static_router(self):
        self.static_router = StaticRouter(local_path=get_abspath('tests/'))
        self.server.set_router('/static', self.static_router)
        # Launch server
        self.server.listen('127.0.0.1', 8080)
        response = self.server.do_request(method='GET',
                                     path='/static/hello.txt',
                                     context=self.context(router=self.static_router, mount_path='/static'))
        assert response.get('status') == 200
        assert response.get('entity') == 'hello world'
        self.server.stop()
    """



if __name__ == '__main__':
    main()
