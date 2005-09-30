# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Piotr Macuk <piotr@macuk.pl>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from Python
import unittest
from unittest import TestCase

# Import from itools
from rss import RSS, TZDateTime
from itools.resources import get_resource
from itools.handlers import get_handler 



class RSSTestCase(TestCase):

    def test_parsing(self):
        in_resource = get_resource('test.rss')
        template = get_handler('test.xml')
        rss = RSS(in_resource)
        html = get_handler('test.html')

        output = template.stl(rss.get_namespace())

        self.assertEqual(output, html.to_str().strip())


    def test_parsing_full(self):
        in_resource = get_resource('test_full.rss')
        template = get_handler('test_full.xml')
        rss = RSS(in_resource)
        html = get_handler('test_full.html')

        output = template.stl(rss.get_namespace())

        self.assertEqual(output, html.to_str().strip())


    def test_to_unicode(self):
        in_resource = get_resource('test2.rss')
        out_resource = get_handler('test2-out.rss')
        rss = RSS(in_resource)
        self.assertEqual(rss.to_unicode(), unicode(out_resource.to_str().strip()))


    def test_namespace(self):
        in_resource = get_resource('test.rss')
        rss = RSS(in_resource)
        ns = rss.get_namespace()
        assert len(ns['channel']['items']) == 2


    def test_datetime(self):
        test_dates = {
            'Tue, 14 Jun 2005 09:00:00 -0400': '2005-06-14 13:00:00',
            'Tue, 14 Jun 2005 09:00:00 +0200': '2005-06-14 07:00:00',
            'Thu, 28 Jul 2005 15:36:55 EDT': '2005-07-28 19:36:55',
            'Fri, 29 Jul 2005 05:50:13 GMT': '2005-07-29 05:50:13',
            '29 Jul 2005 07:27:19 UTC': '2005-07-29 07:27:19',
            '02 Jul 2005 09:52:23 GMT': '2005-07-02 09:52:23'
        }
        for dt, utc in test_dates.items():
            d = TZDateTime.decode(dt)
            self.assertEqual(TZDateTime.encode(d), utc)



if __name__ == '__main__':
    unittest.main()
