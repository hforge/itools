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
from parser import parse_inline


class TestInlineParser(unittest.TestCase):

    def test_bytestring(self):
        """I am a bytestring, not text."""
        data = """I am a bytestring, not text."""
        self.assertRaises(TypeError, parse_inline(data))

    def test_text(self):
        """I am a regular text."""
        data = u"""I am a regular text."""
        events = parse_inline(data).next()
        self.assertEqual(events, ('text', u'I am a regular text.'))


    def test_emphasis(self):
        """This text *contains* emphasis."""
        data = u"""This text *contains* emphasis."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This text '))
        self.assertEqual(events[1], ('emphasis', u'contains'))
        self.assertEqual(events[2], ('text', u' emphasis.'))


    def test_emphasis_strong(self):
        """This text *contains* **strong** emphasis."""
        data = u"""This text *contains* **strong** emphasis."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This text '))
        self.assertEqual(events[1], ('emphasis', u'contains'))
        self.assertEqual(events[2], ('text', u' '))
        self.assertEqual(events[3], ('strong', u'strong'))
        self.assertEqual(events[4], ('text', u' emphasis.'))


    def test_interpreted(self):
        """This `word` is interpreted."""
        data = u"""This `word` is interpreted."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This '))
        self.assertEqual(events[1], ('interpreted', u'word'))
        self.assertEqual(events[2], ('text', u' is interpreted.'))


    def test_inline_literal(self):
        """This ``word`` is inline literal."""
        data = u"""This ``word`` is inline literal."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This '))
        self.assertEqual(events[1], ('literal', u'word'))
        self.assertEqual(events[2], ('text', u' is inline literal.'))


    def test_reference_simple(self):
        """This word_ is a reference to a target."""
        data = u"""This word_ is a reference to a target."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This '))
        self.assertEqual(events[1], ('reference', u'word'))
        self.assertEqual(events[2], ('text', u' is a reference to a target.'))


    def test_reference_quoted(self):
        """This `couple of words`_ is a reference too."""
        data = u"""This `couple of words`_ is a reference too."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This '))
        self.assertEqual(events[1], ('reference', u'couple of words'))
        self.assertEqual(events[2], ('text', u' is a reference too.'))


    def test_not_reference(self):
        """This is a_trap for the ``__parser__``."""
        data = u"""This is a_trap for the ``__parser__``."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'This is a_trap for the '))
        self.assertEqual(events[1], ('literal', u'__parser__'))
        self.assertEqual(events[2], ('text', u'.'))


    def test_fake_footnote(self):
        """I look like a footnote[1]."""
        data = u"""I look like a footnote[1]."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'I look like a footnote'))
        self.assertEqual(events[1], ('text', u'[1].'))


    def test_reference_footnote(self):
        """See the footnote[1]_."""
        data = u"""See the footnote[1]_."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'See the footnote'))
        self.assertEqual(events[1], ('footnote', u'1'))
        self.assertEqual(events[2], ('text', u'.'))


    def test_reference_citation(self):
        """See the citation [CIT2002]_."""
        data = u"""See the citation [CIT2002]_."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'See the citation '))
        self.assertEqual(events[1], ('citation', u'CIT2002'))
        self.assertEqual(events[2], ('text', u'.'))


    def test_reference_substitution(self):
        """Introducing the |substitution|!"""
        data = u"""Introducing the |substitution|!"""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'Introducing the '))
        self.assertEqual(events[1], ('substitution', u'substitution'))
        self.assertEqual(events[2], ('text', u'!'))


    def test_target_inline(self):
        """I am a _`inline target`."""
        data = u"""I am a _`inline target`."""
        events = list(parse_inline(data))
        self.assertEqual(events[0], ('text', u'I am a '))
        self.assertEqual(events[1], ('target', u'inline target'))
        self.assertEqual(events[2], ('text', u'.'))



if __name__ == '__main__':
    unittest.main()
