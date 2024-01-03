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

from collections import OrderedDict
from unittest import TestCase, main

# Import from itools
from itools.web.dispatcher import URIDispatcher


class DispatcherTestCase(TestCase):

    def setUp(self):
        self.dispatcher = URIDispatcher()


    def _check_matching_method(self, urls):
        for url, method in urls:
            method_selected, _ = self.dispatcher.resolve(url)
            assert method_selected == method


    def _register_routes(self, patterns):
        # Clear patterns
        self.dispatcher.patterns = OrderedDict()
        # Register in dispatcher
        for route, method in patterns:
            self.dispatcher.add(route, method)


    def test_pattern_matching(self):
        patterns = [
            ('/one',              'ROUTE1'),
            ('/one/{name}',       'ROUTE11'),
            ('/one/{name}/two',   'ROUTE2'),
            ('/two/three',        'ROUTE3'),
            ('/two/three/{name}', 'ROUTE33'),
            ('/ui/{name:chunk}.{extension:chunk}', 'ROUTEICON'),
            ('/ui/skin/{name:any}', 'ROUTEALL'),
        ]
        match_urls = [
            ('/one',            'ROUTE1'),
            ('/one/hello',      'ROUTE11'),
            ('/one/hello/two',  'ROUTE2'),
            ('/two/three',      'ROUTE3'),
            ('/two/three/test', 'ROUTE33'),
            ('/ui/favicon.ico', 'ROUTEICON'),
            ('/ui/skin/favicon.ico', 'ROUTEALL'),
            ('/ui/skin/images/image.png', 'ROUTEALL'),
        ]
        bad_urls = [
            '/one/',
            'one',
            '/one/hello/test',
            '/hello/two',
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution
        self._check_matching_method(match_urls)
        # Check bad urls
        for url in bad_urls:
            assert self.dispatcher.resolve(url) is None


    def test_patterns_params(self):
        patterns = [
            ('/one/{param:digits}', 'DIGIT'),
            ('/one/{param:number}', 'NUMBER'),
            ('/one/{param:alpha}',  'ALPHA'),
            ('/one/{param:word}',   'WORD'),
            ('/one/{param:chunk}',  'CHUNK'),
            ('/one/{param:any}',    'ANY'),
        ]
        urls = [
            ('/one/14',            'DIGIT'),
            ('/one/14.3',          'NUMBER'),
            ('/one/Hello',         'ALPHA'),
            ('/one/Hello1',        'WORD'),
            ('/one/Hello@1_8',     'CHUNK'),
            ('/one/Hello@1_8/any', 'ANY'),
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution with params
        for url, method in urls:
            method_selected, params = self.dispatcher.resolve(url)
            assert method_selected == method
            assert params.get('param') == url.replace('/one/', '')


    def test_patterns_ordering(self):
        patterns = [
            ('/one/{param}',     'FIRST'),
            ('/one/{param}/two', 'SECOND'),
            ('/one/{param:any}', 'THIRD'),
        ]
        urls = [
            ('/one/test',           'FIRST'),
            ('/one/test/two',       'SECOND'),
            ('/one/test/two/three', 'THIRD'),
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution
        self._check_matching_method(urls)
        # Change ordering to verify catch all effect
        patterns = [
            ('/one/{param:any}', 'FIRST'),
            ('/one/{param}',     'SECOND'),
            ('/one/{param}/two', 'THIRD'),
        ]
        urls = [
            ('/one/test',           'FIRST'),
            ('/one/test/two',       'FIRST'),
            ('/one/test/two/three', 'FIRST'),
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution
        self._check_matching_method(urls)
        # Add special case taking advantage of ordering
        patterns = [
            ('/one/14',             'SPECIAL'),
            ('/one/{param:digits}', 'DIGITS'),
        ]
        urls = [
            ('/one/15',  'DIGITS'),
            ('/one/180', 'DIGITS'),
            ('/one/14',  'SPECIAL'),
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution
        self._check_matching_method(urls)
        # Other way around, special case never caught
        patterns = [
            ('/one/{param:digits}', 'DIGITS'),
            ('/one/14',             'SPECIAL'),
        ]
        urls = [
            ('/one/15',  'DIGITS'),
            ('/one/180', 'DIGITS'),
            ('/one/14',  'DIGITS'),
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution
        self._check_matching_method(urls)


    def test_patterns_override(self):
        patterns = [
            ('/one/{param}', 'FIRST'),
            ('/one/{param}', 'SECOND'),
            ('/one/{param}', 'THIRD'),
        ]
        # Last override method will be called
        urls = [
            ('/one/two',   'THIRD'),
            ('/one/three', 'THIRD'),
        ]
        # Register route patterns
        self._register_routes(patterns)
        # Check dispatcher route resolution
        self._check_matching_method(urls)



if __name__ == '__main__':
    main()

