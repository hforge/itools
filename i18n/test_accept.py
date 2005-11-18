# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2001, 2002 J. David Ibáñez <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


"""
Test suite for the language negotiation stuff.
"""



# Python unit test
import unittest
from unittest import TestCase


# Add the Localizer product directory to the path
import os, sys
sys.path.append(os.path.join(sys.path[0], '../'))

# Localizer modules
from accept import AcceptCharset, AcceptLanguage



class AcceptCharsetTestCase(TestCase):
    def test_case1(self):
        accept = AcceptCharset("ISO-8859-1, utf-8;q=0.66, *;q=0.66")
        assert accept.get_quality('utf-8') == 0.66

    def test_case2(self):
        accept = AcceptCharset("ISO-8859-1, utf-8;q=0.66, *;q=0.66")
        assert accept.get_quality('ISO-8859-1') == 1.0

    def test_case3(self):
        accept = AcceptCharset("utf-8, *;q=0.66")
        assert accept.get_quality('ISO-8859-1') == 0.66

    def test_case4(self):
        accept = AcceptCharset("utf-8")
        assert accept.get_quality('ISO-8859-1') == 1.0




class QualityAcceptLanguageTestCase(TestCase):
    def setUp(self):
        self.al = AcceptLanguage("da, en-gb;q=0.8")

    def test_da(self):
        assert self.al.get_quality('da') == 1.0

    def test_en_gb(self):
        assert self.al.get_quality('en-gb') == 0.8

    def test_en(self):
        assert self.al.get_quality('en') == 0.8

    def test_en_us(self):
        assert self.al.get_quality('en-us') == 0.0


class SelectLanguageAcceptLanguageTestCase(TestCase):
    def setUp(self):
        self.al = AcceptLanguage("da, en-gb;q=0.8")

    def testNone(self):
        """When none of the languages is acceptable."""

        assert self.al.select_language(['en-us', 'es']) == None

    def testImplicit(self):
        """When the prefered language is not explictly set."""

        assert self.al.select_language(['en-us', 'en']) == 'en'

    def testSeveral(self):
        """When there're several accepted languages."""

        assert self.al.select_language(['en-us', 'en', 'da']) == 'da'


class ChangeAcceptLanguageTestCase(TestCase):
    def setUp(self):
        self.al = AcceptLanguage("da, en-gb;q=0.8")

    def testChange(self):
        al = AcceptLanguage("da, en-gb;q=0.8")
        al['es'] = 5.0

        assert al.get_quality('es') == 5.0
        



if __name__ == '__main__':
    unittest.main()
