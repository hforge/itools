# -*- coding: UTF-8 -*-
# Copyright (C) 2002, 2006-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2004 Thierry Fromon <from.t@free.fr>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
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
import unittest

# Import from itools
from itools.html import HTMLParser
from itools.xml.i18n import get_units
from itools.srx import get_segments, Message


class SentenceTestCase(unittest.TestCase):

    def test_simple(self):
        text = u'This is a sentence. A very little sentence.'
        result = [u'This is a sentence.', u'A very little sentence.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(list(segments), result)


    def test_single_character(self):
        text = u'I am T. From.'
        result =  [u'I am T. From.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_abrevations(self):
        # 1
        text = u'This is Toto Inc. a big company.'
        result = [u'This is Toto Inc. a big company.']
        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(list(segments), result)
        # 2
        text = u'Mr. From'
        result =  [u'Mr. From']
        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(list(segments), result)


    def test_between_number(self):
        text = u'Price: -12.25 Euro.'
        result = [u'Price:', u'-12.25 Euro.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_unknown_abrevations(self):
        text = u'E.T. is beautiful.'
        result =  [u'E.T. is beautiful.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_bad_abrevations(self):
        text = u'E.T is beautiful.'
        result =  [u'E.T is beautiful.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_number(self):
        text = u'The 12.54 and 12,54 and 152.'
        result = [u'The 12.54 and 12,54 and 152.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_punctuation(self):
        text = u'A Ph.D in          mathematics?!!!!'
        result = [u'A Ph.D in mathematics?!!!!']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_etc(self):
        text = u'A lot of animals... And no man'
        result = [u'A lot of animals...', u'And no man']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_HTML(self):
        data = '<a ref="; t. ffff">hello </a>      GOGO'

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        result = [u'<a ref="; t. ffff">hello </a> GOGO']
        self.assertEqual(list(segments), result)


    def test_HTMLbis(self):
        data = '<em>J.  David</em>'
        result = [u'J. David']

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_HTML3(self):
        data = '-- toto is here -- *I am*'
        result = [u'-- toto is here -- *I am*']

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_HTML4(self):
        data = ' <a href="http://www.debian.org/"> Debian </a> Hello.  Toto'
        result = [u'<a href="http://www.debian.org/"> Debian </a> Hello.',
                  u'Toto']

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_word(self):
        message = Message()
        message.append_text('Hello. ')

        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(list(segments), [u'Hello.'])


    def test_parentheses1(self):
        text = (
            '(Exception: if the Program itself is interactive but does not'
            ' normally print such an announcement, your work based on the'
            ' Program is not required to print an announcement.)  ')
        result = [u'(Exception:',
            u'if the Program itself is interactive but does not normally'
            u' print such an announcement, your work based on the Program'
            u' is not required to print an announcement.)']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_parentheses2(self):
        text = '(Hereinafter, translation is included without limitation' \
               ' in the term "modification".)  Each licensee is addressed' \
               ' as "you".'
        result = ['(Hereinafter, translation is included without limitation'
                  ' in the term "modification".) Each licensee is addressed'
                  ' as "you".']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_tab(self):
        text = '\n\t   This folder is empty.\n\t   '
        result = ['This folder is empty.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_semicolon(self):
        text = 'Write to the Free Software Foundation; we sometimes make' \
               ' exceptions for this.'
        result = ['Write to the Free Software Foundation;',
                  'we sometimes make exceptions for this.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_newline(self):
        text = 'And you must show them these terms so they know their\n' \
               'rights.\n'
        result = [
            'And you must show them these terms so they know their rights.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(list(segments), result)


    def test_raw_text(self):
        text = u'This is raw text. Every characters must be kept. ' \
               u'1 space 2 spaces  3 spaces   1 newline\nend.'
        expected = [u'This is raw text.', u'Every characters must be kept.',
                    u'1 space 2 spaces  3 spaces   1 newline\nend.']

        message = Message()
        message.append_text(text)
        segments = []
        for seg, offset in get_segments(message, keep_spaces=True):
            segments.append(seg)

        self.assertEqual(list(segments), expected)


    def test_surrounding_format(self):
        data = '<em>Surrounding format elements should be extracted !</em>'
        expected = [u'Surrounding format elements should be extracted !']

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(list(segments), expected)


    def test_ignore_tags(self):
        data = 'Hello <em> Baby.</em> How are you ?'
        expected = [u'Hello <em> Baby.</em>', u'How are you ?']

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(list(segments), expected)


    def test_iter_segmentation(self):
        """Here is a message surrounded by format elements and which contains
        others segments. The segments must be well extracted by the iterative
        algorithm."""

        data = '<span>This text contains many sentences. A sentence. ' \
               'Another one. This text must be well segmented.  </span>'
        expected = [u'This text contains many sentences.', u'A sentence.',
                    u'Another one.', u'This text must be well segmented.']

        segments = []
        for seg, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(list(segments), expected)


if __name__ == '__main__':
    unittest.main()
