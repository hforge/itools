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


class View(BaseView):

    access = True

    def GET(self, resource, context):
        context.set_content_type('text/plain')
        return 'Welcome ' + context.path_query_base.get('name')



class Database(object):

    has_changed = False


class Root(object):

    context_cls = Context

    def before_traverse(self, context):
        pass

    def after_traverse(self, context):
        pass

    def get_resource(self, path, soft=False):
        return self


SERVER = None

class RouterTestCase(TestCase):

    def setUp(self):
        global SERVER
        # Init context
        self.context = Context(root=Root(), database=Database())
        if SERVER is None:
            SERVER = WebServer(root=Root())
            SERVER.listen('127.0.0.1', 8080)


    def test_dispatch_router(self):
        global SERVER
        SERVER.dispatcher.add('/rest/welcome/{name}', View)
        # Check good request
        response = SERVER.do_request(method='GET',
                                     path='/rest/welcome/test',
                                     context=self.context())
        assert response.get('status') == 200
        assert response.get('entity') == 'Welcome test'


if __name__ == '__main__':
    main()
