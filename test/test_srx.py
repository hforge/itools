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
from itools.srx import get_segments, Message, TEXT, START_FORMAT, END_FORMAT


class SentenceTestCase(unittest.TestCase):

    def test_simple(self):
        text = u'This is a sentence. A very little sentence.'
        result =[((TEXT, u'This is a sentence.'),),
                 ((TEXT, u'A very little sentence.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, result)


    def test_single_character(self):
        text = u'I am T. From.'
        result = [((TEXT, u'I am T. From.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_abrevations(self):
        # 1
        text = u'This is Toto Inc. a big company.'
        result = [((TEXT, u'This is Toto Inc. a big company.'),)]
        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, result)
        # 2
        text = u'Mr. From'
        result =  [((TEXT, u'Mr. From'),)]
        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, result)


    def test_between_number(self):
        text = u'Price: -12.25 Euro.'
        result = [((TEXT, u'Price:'),), ((TEXT, u'-12.25 Euro.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_unknown_abrevations(self):
        text = u'E.T. is beautiful.'
        result = [((TEXT, u'E.T. is beautiful.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_bad_abrevations(self):
        text = u'E.T is beautiful.'
        result =  [((TEXT, u'E.T is beautiful.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_number(self):
        text = u'The 12.54 and 12,54 and 152.'
        result = [((TEXT, u'The 12.54 and 12,54 and 152.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_punctuation(self):
        text = u'A Ph.D in          mathematics?!!!!'
        result =  [((TEXT, u'A Ph.D in mathematics?!!!!'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_etc(self):
        text = u'A lot of animals... And no man'
        result = [((TEXT, u'A lot of animals...'),), ((TEXT, u'And no man'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_HTML(self):
        data = '<a href="; t. ffff">hello </a>      GOGO'

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        result = [((START_FORMAT, 1), (TEXT, u'hello '), (END_FORMAT, 1),
                   (TEXT, u' GOGO'))]
        self.assertEqual(segments, result)


    def test_HTMLbis(self):
        data = '<em>J.  David</em>'
        result = [((TEXT, u'J. David'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_HTML3(self):
        data = '-- toto is here -- *I am*'
        result = [((TEXT, u'-- toto is here -- *I am*'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_HTML4(self):
        data = ' <a href="http://www.debian.org/"> Debian </a> Hello.  Toto'
        result =  [((START_FORMAT, 1), (TEXT, u' Debian '), (END_FORMAT, 1),
                    (TEXT, u' Hello.')), ((TEXT, u'Toto'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_word(self):
        message = Message()
        message.append_text('Hello. ')

        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, [((TEXT, u'Hello.'),)])


    def test_parentheses1(self):
        text = (
            '(Exception: if the Program itself is interactive but does not'
            ' normally print such an announcement, your work based on the'
            ' Program is not required to print an announcement.)  ')
        result = [((TEXT, u'(Exception:'),),
                  ((TEXT, u'if the Program itself is interactive but does '
                          u'not normally print such an announcement, your '
                          u'work based on the Program is not required to '
                          u'print an announcement.)'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_parentheses2(self):
        text = '(Hereinafter, translation is included without limitation' \
               ' in the term "modification".)  Each licensee is addressed' \
               ' as "you".'
        result = [((TEXT, u'(Hereinafter, translation is included without '
                          u'limitation in the term "modification".) Each '
                          u'licensee is addressed as "you".'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_tab(self):
        text = '\n\t   This folder is empty.\n\t   '
        result = [((TEXT, u'This folder is empty.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_semicolon(self):
        text = 'Write to the Free Software Foundation; we sometimes make' \
               ' exceptions for this.'
        result =  [((TEXT, u'Write to the Free Software Foundation;'),),
                   ((TEXT, u'we sometimes make exceptions for this.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_newline(self):
        text = 'And you must show them these terms so they know their\n' \
               'rights.\n'
        result = [((TEXT,
          u'And you must show them these terms so they know their rights.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_raw_text(self):
        text = u'This is raw text. Every characters must be kept. ' \
               u'1 space 2 spaces  3 spaces   1 newline\nend.'
        expected = [((TEXT, u'This is raw text.'),),
                    ((TEXT, u'Every characters must be kept.'),),
                    ((TEXT, u'1 space 2 spaces  3 spaces   1 newline\nend.'),)
                    ]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message, keep_spaces=True):
            segments.append(seg)

        self.assertEqual(segments, expected)


    def test_surrounding_format(self):
        data = '<em>Surrounding format elements should be extracted !</em>'
        expected =[((TEXT,
                     u'Surrounding format elements should be extracted !'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(segments, expected)


    def test_ignore_tags(self):
        data = 'Hello <em> Baby.</em> How are you ?'
        expected = [((TEXT, u'Hello '), (START_FORMAT, 1), (TEXT, u' Baby.'),
                     (END_FORMAT, 1)), ((TEXT, u'How are you ?'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(segments, expected)


    def test_iter_segmentation(self):
        """Here is a message surrounded by format elements and which contains
        others segments. The segments must be well extracted by the iterative
        algorithm."""

        data = '<span>This text contains many sentences. A sentence. ' \
               'Another one. This text must be well segmented.  </span>'
        expected = [((TEXT, u'This text contains many sentences.'),),
                    ((TEXT, u'A sentence.'),), ((TEXT, u'Another one.'),),
                    ((TEXT, u'This text must be well segmented.'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(segments, expected)


if __name__ == '__main__':
    unittest.main()
