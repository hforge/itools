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
from itools.uri import Reference
from itools.xml import XMLParser, XML_DECL
from itools.rss import RSSFile



class RSSTestCase(TestCase):
    """Only testing required attributes, the logic behind is the same for
    all kinds.
    """

    def setUp(self):
        self.rss = RSSFile('sample-rss-2.xml')


    def test_channel(self):
        channel = self.rss.channel
        self.assertEqual(channel['title'], u"Liftoff News")
        link = channel['link']
        self.assert_(isinstance(link, Reference))
        self.assertEqual(str(link), 'http://liftoff.msfc.nasa.gov/')
        self.assertEqual(channel['description'],
                u"Liftoff to Space Exploration.")


    def test_image(self):
        # TODO Our sample actually don't have an image
        self.assertEqual(self.rss.image, None)


    def test_items(self):
        items = self.rss.items
        self.assertEqual(len(items), 4)


    def test_item(self):
        item = self.rss.items[0]
        self.assertEqual(item['title'], u"Star City")
        link = item['link']
        self.assert_(isinstance(link, Reference))
        self.assertEqual(str(link),
                'http://liftoff.msfc.nasa.gov/news/2003/news-starcity.asp')
        expected = u"How do Americans get ready to work with Russians"
        self.assert_(item['description'].startswith(expected))


    def test_serialize(self):
        data = self.rss.to_str()
        # Testing the hand-written XML is well-formed
        events = list(XMLParser(data))
        # Testing the XML processing instruction
        event, value, line_number = events[0]
        self.assertEqual(event, XML_DECL)
        version, encoding, standalone = value
        self.assertEqual(version, '1.0')
        self.assertEqual(encoding, 'UTF-8')


    def tearDown(self):
        del self.rss



if __name__ == '__main__':
    unittest.main()
