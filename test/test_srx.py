# -*- coding: UTF-8 -*-
# Copyright (C) 2002, 2006-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2004 Thierry Fromon <from.t@free.fr>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from unittest import TestCase, main

# Import from itools
from itools.html import HTMLParser
from itools.srx import get_segments, Message, TEXT, START_FORMAT, END_FORMAT
from itools.xmlfile import get_units


class SentenceTestCase(TestCase):

    def test_simple(self):
        text = 'This is a sentence. A very little sentence.'
        result =[((TEXT, 'This is a sentence.'),),
                 ((TEXT, 'A very little sentence.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, result)


    def test_single_character(self):
        text = 'I am T. From.'
        result = [((TEXT, 'I am T. From.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_abrevations(self):
        # 1
        text = 'This is Toto Inc. a big company.'
        result = [((TEXT, 'This is Toto Inc. a big company.'),)]
        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, result)
        # 2
        text = 'Mr. From'
        result =  [((TEXT, 'Mr. From'),)]
        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)
        self.assertEqual(segments, result)


    def test_between_number(self):
        text = 'Price: -12.25 Euro.'
        result = [((TEXT, 'Price:'),), ((TEXT, '-12.25 Euro.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_unknown_abrevations(self):
        text = 'E.T. is beautiful.'
        result = [((TEXT, 'E.T. is beautiful.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_bad_abrevations(self):
        text = 'E.T is beautiful.'
        result =  [((TEXT, 'E.T is beautiful.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_number(self):
        text = 'The 12.54 and 12,54 and 152.'
        result = [((TEXT, 'The 12.54 and 12,54 and 152.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_punctuation(self):
        text = 'A Ph.D in          mathematics?!!!!'
        result =  [((TEXT, 'A Ph.D in mathematics?!!!!'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_etc(self):
        text = 'A lot of animals... And no man'
        result = [((TEXT, 'A lot of animals...'),), ((TEXT, 'And no man'),)]

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

        result = [((START_FORMAT, 1), (TEXT, 'hello '), (END_FORMAT, 1),
                   (TEXT, ' GOGO'))]
        self.assertEqual(segments, result)


    def test_HTMLbis(self):
        data = '<em>J.  David</em>'
        result = [((TEXT, 'J. David'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_HTML3(self):
        data = '-- toto is here -- *I am*'
        result = [((TEXT, '-- toto is here -- *I am*'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_HTML4(self):
        data = ' <a href="http://www.debian.org/"> Debian </a> Hello.  Toto'
        result =  [((START_FORMAT, 1), (TEXT, ' Debian '), (END_FORMAT, 1),
                    (TEXT, ' Hello.')), ((TEXT, 'Toto'),)]

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
        self.assertEqual(segments, [((TEXT, 'Hello.'),)])


    def test_parentheses1(self):
        text = (
            '(Exception: if the Program itself is interactive but does not'
            ' normally print such an announcement, your work based on the'
            ' Program is not required to print an announcement.)  ')
        result = [((TEXT, '(Exception:'),),
                  ((TEXT, 'if the Program itself is interactive but does '
                          'not normally print such an announcement, your '
                          'work based on the Program is not required to '
                          'print an announcement.)'),)]

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
        result = [((TEXT, '(Hereinafter, translation is included without '
                          'limitation in the term "modification".) Each '
                          'licensee is addressed as "you".'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_tab(self):
        text = '\n\t   This folder is empty.\n\t   '
        result = [((TEXT, 'This folder is empty.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_semicolon(self):
        text = 'Write to the Free Software Foundation; we sometimes make' \
               ' exceptions for this.'
        result =  [((TEXT, 'Write to the Free Software Foundation;'),),
                   ((TEXT, 'we sometimes make exceptions for this.'),)]

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
          'And you must show them these terms so they know their rights.'),)]

        message = Message()
        message.append_text(text)
        segments = []
        for seg, context, offset in get_segments(message):
            segments.append(seg)

        self.assertEqual(segments, result)


    def test_raw_text(self):
        text = 'This is raw text. Every characters must be kept. ' \
               '1 space 2 spaces  3 spaces   1 newline\nend.'
        expected = [((TEXT, 'This is raw text.'),),
                    ((TEXT, 'Every characters must be kept.'),),
                    ((TEXT, '1 space 2 spaces  3 spaces   1 newline\nend.'),)
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
                     'Surrounding format elements should be extracted !'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(segments, expected)


    def test_ignore_tags(self):
        data = 'Hello <em> Baby.</em> How are you ?'
        expected = [((TEXT, 'Hello '), (START_FORMAT, 1), (TEXT, ' Baby.'),
                     (END_FORMAT, 1)), ((TEXT, 'How are you ?'),)]

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
        expected = [((TEXT, 'This text contains many sentences.'),),
                    ((TEXT, 'A sentence.'),), ((TEXT, 'Another one.'),),
                    ((TEXT, 'This text must be well segmented.'),)]

        segments = []
        for seg, context, offset in get_units(HTMLParser(data)):
            segments.append(seg)
        self.assertEqual(segments, expected)


if __name__ == '__main__':
    main()
