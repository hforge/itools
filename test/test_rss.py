# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from Python
import unittest
from unittest import TestCase

# Import from itools
from itools.rss.rss import RSS
from itools.handlers import get_handler
from itools.stl import stl



class RSSTestCase(TestCase):

    def test_parsing(self):
        template = get_handler('test.xml')
        rss = RSS('test.rss')
        html = get_handler('test.html')

        output = stl(template, rss.get_namespace())

        self.assertEqual(output, html.to_str().strip())


    def test_parsing_full(self):
        template = get_handler('test_full.xml')
        rss = RSS('test_full.rss')
        html = get_handler('test_full.html')

        output = stl(template, rss.get_namespace())

        self.assertEqual(output, html.to_str().strip())


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
