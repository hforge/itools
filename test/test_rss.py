# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from Python
import unittest
from unittest import TestCase

# Import from itools
from itools.rss import RSS
from itools.handlers import get_handler
from itools.stl import stl



class RSSTestCase(TestCase):

    def test_parsing(self):
        rss = RSS('test.rss')
        template = get_handler('test.xml')
        output = stl(template, rss.get_namespace())

##        html = get_handler('test.html')
##        self.assertEqual(output, html.to_str().strip())


    def test_parsing_full(self):
        rss = RSS('test_full.rss')
        template = get_handler('test_full.xml')
        output = stl(template, rss.get_namespace())

##        html = get_handler('test_full.html')
##        self.assertEqual(output, html.to_str().strip())


    def test_to_str(self):
        out_resource = get_handler('test2-out.rss')
        rss = RSS('test2.rss')
        self.assertEqual(rss.to_str(), out_resource.to_str().strip())


    def test_namespace(self):
        rss = RSS('test.rss')
        ns = rss.get_namespace()
        self.assertEqual(len(ns['channel']['items']), 2)



if __name__ == '__main__':
    unittest.main()
