# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002, 2003 J. David Ibáñez <jdavid@itaapy.com>
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
from sets import Set
import unittest
from unittest import TestCase

# Import from itools
from itools.resources import memory
from PO import PO
import XHTML



class SegmentationTestCase(TestCase):
    def test_paragraph(self):
        """Test formatted paragraph"""
        data = '<p xmlns="http://www.w3.org/1999/xhtml">\n' \
               'The Mozilla project maintains <em>choice</em> and\n' \
               '<em>innovation</em> on the Internet. Developing the\n' \
               'acclaimed, <em>open source</em>, <b>Mozilla 1.6</b>.\n' \
               '</p>'
        resource = memory.File(data)
        doc = XHTML.Document(resource)

        expected = [u'The Mozilla project maintains <em>choice</em> and'
                    u' <em>innovation</em> on the Internet.',
                    u'Developing the acclaimed, <em>open source</em>,'
                    u' <b>Mozilla 1.6</b>.']
        self.assertEqual(doc.get_messages(), Set(expected))


    def test_table(self):
        data = '<table xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <tr>\n' \
               '    <th>Title</th>\n' \
               '    <th>Size</th>\n' \
               '  </tr>\n' \
               '  <tr>\n' \
               '    <td>The good, the bad and the ugly</td>\n' \
               '    <td>looong</td>\n' \
               '  </tr>\n' \
               '  <tr>\n' \
               '    <td>Love story</td>\n' \
               '    <td>even longer</td>\n' \
               '  </tr>\n' \
               '</table>'
        resource = memory.File(data)
        doc = XHTML.Document(resource)

        expected = [u'Title', u'Size',
                    u'The good, the bad and the ugly', u'looong',
                    u'Love story', u'even longer']
        self.assertEqual(doc.get_messages(), Set(expected))


    def test_random(self):
        """Test element content."""
        # The document
        data = '<body xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <p>this <em>word</em> is nice</p>\n' \
               '  <a href="/"><img src="logo.png" /></a>\n' \
               '  <p><em>hello world</em></p><br/>' \
               '  bye <em>J. David Ibanez Palomar</em>\n' \
               '</body>'
        resource = memory.File(data)
        doc = XHTML.Document(resource)

        messages = doc.get_messages()
        expected = [u'this <em>word</em> is nice',
                    u'hello world',
                    u'bye <em>J. David Ibanez Palomar</em>']
        self.assertEqual(doc.get_messages(), Set(expected))


    def test_form(self):
        """Test complex attribute."""
        # The document
        data = '<form xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <input type="text" name="id" />\n' \
               '  <input type="submit" value="Change" />\n' \
               '</form>'
        resource = memory.File(data)
        doc = XHTML.Document(resource)

        messages = doc.get_messages()
        self.assertEqual(messages, Set([u'Change']))
        



if __name__ == '__main__':
    unittest.main()
