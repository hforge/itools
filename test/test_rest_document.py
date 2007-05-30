#!/usr/bin/env python2.5
# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
import unittest

# Import from itools.rest
from itools.rest.parser import Document


class TestDocumentParser(unittest.TestCase):

    def test_blocks(self):
        text = u"""\
I am a block.

I am another
block."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], ('block', [u'I am a block.', u'']))
        self.assertEqual(events[1], ('block', [u'I am another', u'block.']))


    def test_single_lists(self):
        text = u"""\
* I am an unordered list item
  on several lines.

1. I am an ordered list item
   on several lines."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_lists(events)
        self.assertEqual(len(events), 10)
        self.assertEqual(events[0], ('list_begin', u'*'))
        self.assertEqual(events[1], ('list_item_begin', 2))
        self.assertEqual(events[2], ('block', [u'I am an unordered list item', u'  on several lines.', u'']))
        self.assertEqual(events[3], ('list_item_end', 2))
        self.assertEqual(events[4], ('list_end', u'*'))
        self.assertEqual(events[5], ('list_begin', u'#'))
        self.assertEqual(events[6], ('list_item_begin', 3))
        self.assertEqual(events[7], ('block', [u'I am an ordered list item', u'   on several lines.']))
        self.assertEqual(events[8], ('list_item_end', 3))
        self.assertEqual(events[9], ('list_end', u'#'))


    def test_double_lists(self):
        text = u"""\
* I am an unordered list item;

* on several lines.

1. I am an ordered list item;

2. on several lines."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_lists(events)
        self.assertEqual(len(events), 16)
        self.assertEqual(events[0], ('list_begin', u'*'))
        self.assertEqual(events[1], ('list_item_begin', 2))
        self.assertEqual(events[2], ('block', [u'I am an unordered list item;', u'']))
        self.assertEqual(events[3], ('list_item_end', 2))
        self.assertEqual(events[4], ('list_item_begin', 2))
        self.assertEqual(events[5], ('block', [u'on several lines.', u'']))
        self.assertEqual(events[6], ('list_item_end', 2))
        self.assertEqual(events[7], ('list_end', u'*'))
        self.assertEqual(events[8], ('list_begin', u'#'))
        self.assertEqual(events[9], ('list_item_begin', 3))
        self.assertEqual(events[10], ('block', [u'I am an ordered list item;', u'']))
        self.assertEqual(events[11], ('list_item_end', 3))
        self.assertEqual(events[12], ('list_item_begin', 3))
        self.assertEqual(events[13], ('block', [u'on several lines.']))
        self.assertEqual(events[14], ('list_item_end', 3))
        self.assertEqual(events[15], ('list_end', u'#'))


    def test_nested_lists(self):
        text = u"""\
* First list.

  1. Second list.

     Second list, second paragraph.

  First list, second paragraph."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_lists(events)
        self.assertEqual(len(events), 12)
        self.assertEqual(events[0], ('list_begin', u'*'))
        self.assertEqual(events[1], ('list_item_begin', 2))
        self.assertEqual(events[2], ('block', [u'First list.', u'']))
        self.assertEqual(events[3], ('list_begin', u'#'))
        self.assertEqual(events[4], ('list_item_begin', 5))
        self.assertEqual(events[5], ('block', [u'Second list.', u'']))
        self.assertEqual(events[6], ('block', [u'     Second list, second paragraph.', u'']))
        self.assertEqual(events[7], ('list_item_end', 5))
        self.assertEqual(events[8], ('list_end', u'#'))
        self.assertEqual(events[9], ('block', [u'  First list, second paragraph.']))
        self.assertEqual(events[10], ('list_item_end', 2))
        self.assertEqual(events[11], ('list_end', u'*'))


    def test_literal_blocks(self):
        text = u"""\
The code reads as follow::

    >>> from itools.rest import parser

But failed with a NotImplementedError."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_literal_blocks(events)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], ('block', [u'The code reads as follow:']))
        self.assertEqual(events[1], ('literal_block', u'    >>> from itools.rest import parser'))
        self.assertEqual(events[2], ('block', [u'But failed with a NotImplementedError.']))


    def test_list_literal(self):
        text = u"""\
1. I am a list
   containing a literal::

     >>> from itools.rest import parser

2. and several
   items."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_lists(events)
        events = Document.parse_literal_blocks(events)
        self.assertEqual(len(events), 9)
        self.assertEqual(events[0], ('list_begin', u'#'))
        self.assertEqual(events[1], ('list_item_begin', 3))
        self.assertEqual(events[2], ('block', [u'I am a list',  u'   containing a literal:']))
        self.assertEqual(events[3], ('literal_block', u'     >>> from itools.rest import parser'))
        self.assertEqual(events[4], ('list_item_end', 3))
        self.assertEqual(events[5], ('list_item_begin', 3))
        self.assertEqual(events[6], ('block', [u'and several',  u'   items.']))
        self.assertEqual(events[7], ('list_item_end', 3))
        self.assertEqual(events[8], ('list_end', u'#'))


    def test_paragraph(self):
        text = u"""\
I am a paragraph.

I am another one."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_titles(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], ('paragraph', u'I am a paragraph.'))
        self.assertEqual(events[1], ('paragraph', u'I am another one.'))


    def test_title_overline(self):
        text = u"""\
#############################
I am the king of the titles
#############################"""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_titles(events)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0],
                         ('title', (u'#', u'I am the king of the titles', u'#')))


    def test_title_underline(self):
        text = u"""\
I am the prince of the titles
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%"""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_titles(events)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0],
                         ('title', (u'', u'I am the prince of the titles', u'%')))


    def test_title_paragraph(self):
        text = u"""\
Please allow to introduce myself
````````````````````````````````
I'm a man of wealth and taste"""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_titles(events)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0],
                        ('title', (u'', u'Please allow to introduce myself', u'`')))
        self.assertEqual(events[1], ('paragraph', u"I'm a man of wealth and taste"))


    def test_paragraph_literal(self):
        text = u"""\
The code reads as follow::

    >>> from itools.rest import parser

But failed with a NotImplementedError."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_literal_blocks(events)
        events = Document.parse_titles(events)
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0], ('paragraph', u'The code reads as follow:'))
        self.assertEqual(events[1], ('literal_block', u'    >>> from itools.rest import parser'))
        self.assertEqual(events[2], ('paragraph', u'But failed with a NotImplementedError.'))


    def test_paragraph_list(self):
        text = u"""\
* I am a block.

  I am the same block.

I am a paragraph."""
        events = [('text', text)]
        events = Document.parse_blocks(events)
        events = Document.parse_lists(events)
        events = Document.parse_titles(events)
        self.assertEqual(len(events), 7)
        self.assertEqual(events[0], ('list_begin', u'*'))
        self.assertEqual(events[1], ('list_item_begin', 2))
        self.assertEqual(events[2], ('paragraph', u'I am a block.'))
        self.assertEqual(events[3], ('paragraph', u'  I am the same block.'))
        self.assertEqual(events[4], ('list_item_end', 2))
        self.assertEqual(events[5], ('list_end', u'*'))
        self.assertEqual(events[6], ('paragraph', u'I am a paragraph.'))





if __name__ == '__main__':
    unittest.main()
