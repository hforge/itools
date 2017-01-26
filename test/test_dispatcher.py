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
from itools.web.dispatcher import URIDispatcher


class DispatcherTestCase(TestCase):

    def test_pattern_matching(self):
        patterns = [
            ('/one',              'ROUTE1'),
            ('/one/{name}',       'ROUTE11'),
            ('/one/{name}/two',   'ROUTE2'),
            ('/two/three',        'ROUTE3'),
            ('/two/three/{name}', 'ROUTE33'),
            ('/ui/{name}', 'ROUTEALL'),
        ]
        match_urls = [
            ('/one',            'ROUTE1'),
            ('/one/hello',      'ROUTE11'),
            ('/one/hello/two',  'ROUTE2'),
            ('/two/three',      'ROUTE3'),
            ('/two/three/test', 'ROUTE33'),
            ('/ui/favicon.ico', 'ROUTEALL'),
            ('/ui/images/image.png', 'ROUTEALL'),
        ]
        bad_urls = [
            '/one/',
            'one',
            '/one/hello/test',
            '/hello/two',
        ]
        dispatcher = URIDispatcher()
        # Register route patterns
        for route, method in patterns:
            dispatcher.add(route, method)
        # Check dispatcher route resolution
        for url, method in match_urls:
            method_selected, _ = dispatcher.select(url)
            assert method_selected == method
        # Check bad urls
        for url in bad_urls:
            assert dispatcher.select(url) is None


    def test_patterns_params(self):
        patterns = [
            ('/one/{param:digits}', 'DIGIT'),
            ('/one/{param:number}', 'NUMBER'),
            ('/one/{param:alpha}',  'ALPHA'),
            ('/one/{param:word}',   'WORD'),
            ('/one/{param:any}',    'ANY'),
        ]
        urls = [
            ('/one/14',       'DIGIT'),
            ('/one/14.3',     'NUMBER'),
            ('/one/Hello',    'ALPHA'),
            ('/one/Hello1',   'WORD'),
            ('/one/Hello@1_', 'ANY'),
            ('/ui/favicon.ico', 'ALL'),
        ]
        dispatcher = URIDispatcher()
        # clear dispatcher
        dispatcher.patterns = []
        # Register route patterns
        for route, method in patterns:
            dispatcher.add(route, method)
        # Check dispatcher route resolution with params
        for url, method in urls:
            method_selected, params = dispatcher.select(url)
            assert method_selected == method
            assert params.get('param') == url.split('/')[-1]



if __name__ == '__main__':
    main()
