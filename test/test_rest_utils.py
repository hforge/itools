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
from itools.rest.parser import strip_block, normalize_whitespace


class TestParserUtils(unittest.TestCase):

    def test_strip_block_empty(self):
        block = []
        stripped = strip_block(block)
        self.assertEqual(stripped, [])


    def test_strip_block_regular(self):
        block = [u"A test", u""]
        stripped = strip_block(block)
        self.assertEqual(stripped, [u"A test"])


    def test_strip_block_whitespace(self):
        block = [u"A test", u"  "]
        stripped = strip_block(block)
        self.assertEqual(stripped, [u"A test"])


    def test_strip_block_tab(self):
        block = [u"A test", u"\t"]
        stripped = strip_block(block)
        self.assertEqual(stripped, [u"A test"])


    def test_normalize_whitespace(self):
        text = u"""  I am   full
of\tinsignificant  \t whitespace. """
        text = normalize_whitespace(text)
        self.assertEqual(text, u"I am full of insignificant whitespace.")



if __name__ == '__main__':
    unittest.main()
