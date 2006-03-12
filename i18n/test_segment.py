# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 J. Thierry Fromon <from.t@free.fr>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import unittest

# Import from itools
from segment import Message


class SentenceTestCase(unittest.TestCase):

    def test_simple(self):
        text = u"This is a sentence. A very little sentence."
        result = [u'This is a sentence.', 'A very little sentence.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_single_character(self):
        text = u"""I am T. From."""
        result =  [u'I am T. From.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_abrevations(self):
        text = u"This is Toto Inc. a big compagny."
        result = [u'This is Toto Inc. a big compagny.']
        text2 = u"Mr. From"
        result2 =  [u'Mr. From']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)
        segments = Message(text2).get_segments()
        self.assertEqual(list(segments), result2)


    def test_between_number(self):
        text = u"Price: -12.25 Euro."
        result = [u'Price: -12.25 Euro.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_unknown_abrevations(self):
        text = u"E.T. is beautiful."
        result =  [u'E.T. is beautiful.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_bad_abrevations(self):
        text = u"E.T is beautiful."
        result =  [u'E.T is beautiful.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_number(self):
        text = u"The 12.54 and 12,54 and 152."
        result = [u'The 12.54 and 12,54 and 152.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_punctuation(self):
        text = u"A Ph.D in          mathematics?!!!!"
        result = [u'A Ph.D in mathematics?!!!!']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_etc(self):
        text = u"A lot of animals... And no man"
        result = [u'A lot of animals...', u'And no man']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)
        #self.assertRaises((AttributeError, TypeError), sentence.get_segments, 1)


    def test_HTML(self):
        text = u""" <a ref="; t. ffff">hello </a>      GOGO """
        result = [u'<a ref="; t. ffff">hello </a> GOGO']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_HTMLbis(self):
        text = u"""<em>J.  David</em>"""
        result = [u'<em>J. David</em>']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_HTML3(self):
        text = u"""-- toto is here-- *I am*"""
        result = [u'-- toto is here-- *I am*']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_HTML3(self):
        text = u""" <a href="http://www.debian.org/"> Debian </a> Hello. Toto"""
        result = [u'<a href="http://www.debian.org/"> Debian </a> Hello.', u'Toto']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_word(self):
        text = 'Hello. '
        result = ['Hello.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_parentheses1(self):
        text = '(Exception: if the Program itself is interactive but does' \
               ' not normally print such an announcement, your work based' \
               ' on the Program is not required to print an announcement.)  '
        result = ['(Exception: if the Program itself is interactive but does'
                  ' not normally print such an announcement, your work based'
                  ' on the Program is not required to print an announcement.)']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_parentheses2(self):
        text = '(Hereinafter, translation is included without limitation' \
               ' in the term "modification".)  Each licensee is addressed' \
               ' as "you".'
        result = ['(Hereinafter, translation is included without limitation'
                  ' in the term "modification".)',
                  'Each licensee is addressed as "you".']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_tab(self):
        text = '\n\t   <em>This folder is empty.</em>\n\t   '
        result = ['<em>This folder is empty.</em>']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_semicolon(self):
        text = 'Write to the Free Software Foundation; we sometimes make' \
               ' exceptions for this.'
        result = ['Write to the Free Software Foundation;',
                  'we sometimes make exceptions for this.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)


    def test_newline(self):
        text = 'And you must show them these terms so they know their\n' \
               'rights.\n'
        result = ['And you must show them these terms so they know their'
                  'rights.']
        segments = Message(text).get_segments()
        self.assertEqual(list(segments), result)



if __name__ == '__main__':
    unittest.main()
