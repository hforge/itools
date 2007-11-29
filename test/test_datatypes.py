# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from datetime import time, date, datetime
import unittest
from unittest import TestCase
import random, decimal

# Import from itools
from itools.datatypes import (ISOTime, ISOCalendarDate, ISODateTime,
                              InternetDateTime,
                              Integer, Decimal, Boolean,
                              Unicode, URI, Email,
                              FileName, QName, Tokens,
                              Enumerate,
                              XML,
                              XMLAttribute)


class BasicTypeTest(TestCase):

    def test_Integer(self):
        for x in range(-10,11):
            data = Integer.encode(x)
            self.assertEqual(x, Integer.decode(data))


    def test_Decimal(self):
        for x in [random.uniform(-100,100) for _ in xrange(10)]:
            x = decimal.Decimal(str(x))
            data = Decimal.encode(x)
            self.assertEqual(x, Decimal.decode(data))


    def test_Unicode(self):
        x = u'العربيه 中文 Español Français'
        data = Unicode.encode(x)
        self.assertEqual(x, Unicode.decode(data))


    def test_Boolean(self):
        for x in [True, False]:
            data = Boolean.encode(x)
            self.assertEqual(x, Boolean.decode(data))


    def test_URI(self):
        for x in ['http://itaapy.com/', 'file:///home/david/texte.txt',
                  '../a/b/', '/a/b/c']:
            data = URI.decode(x)
            self.assertEqual(x, URI.encode(data))


    def test_Email(self):
        for name, result in {'toto.titi@libre.fr':True,
                             'toto@':False}.iteritems():
            self.assertEqual(Email.is_valid(name), result)


    def test_FileName(self):
        for name, result in {'index.html.en':('index', 'html', 'en'),
                             'index.html':('index', 'html', None),
                             'index':('index', None, None)}.iteritems():
            self.assertEqual(FileName.decode(name), result)
            self.assertEqual(FileName.encode(result), name)


    def test_QName(self):
        for name, result in {'pithiviers':(None, 'pithiviers'),
                             'gateau:framboisier': ('gateau', 'framboisier')
                             }.iteritems():
            self.assertEqual(QName.decode(name), result)
            self.assertEqual(QName.encode(result), name)


    def test_Tokens(self):
        data = 'value1 value2 value3'
        result = ('value1', 'value2', 'value3')
        self.assertEqual(Tokens.decode(data), result)
        self.assertEqual(Tokens.encode(result), data)



class EnumerateTestCase(TestCase):

    class AnEnumerate(Enumerate):
        options = [{'name':'name1', 'value':'value1'},
                   {'name':'name2', 'value':'value2'},
                   {'name':'name3', 'value':'value3'}]


    def test_get_options(self):
        self.assertEqual(self.AnEnumerate.get_options(),
                         self.AnEnumerate.options)


    def test_is_valid(self):
        self.assertEqual(self.AnEnumerate.is_valid('name2'), True)
        self.assertEqual(self.AnEnumerate.is_valid('name4'), False)


    def test_get_namespace(self):
        result = self.AnEnumerate.get_namespace(['name1', 'name2', 'name4'])
        self.assertEqual([d['selected'] for d in result],
                         [ True, True, False])


    def test_get_value(self):
        for i in xrange(1,4):
            self.assertEqual(self.AnEnumerate.get_value(
                                'name%d' % i),
                                'value%d' % i)
            self.assertEqual(self.AnEnumerate.get_value('name4'), None)



class ISOTimeTestCase(TestCase):

    def test_time_decode(self):
        data = '13:45:30'
        value = ISOTime.decode(data)
        expected = time(13, 45, 30)
        self.assertEqual(value, expected)

        data = '13:45'
        value = ISOTime.decode(data)
        expected = time(13, 45)
        self.assertEqual(value, expected)


    def test_time_encode(self):
        data = time(13, 45, 30)
        value = ISOTime.encode(data)
        expected = '13:45:30'
        self.assertEqual(value, expected)

        data = time(13, 45)
        value = ISOTime.encode(data)
        expected = '13:45:00'
        self.assertEqual(value, expected)

        data = time(13, 45)
        value = ISOTime.encode(data)
        expected = '13:45:00'
        self.assertEqual(value, expected)


class ISOCalendarDateTestCase(TestCase):

    def test_date_decode(self):
        data = '1975-05-07'
        value = ISOCalendarDate.decode(data)
        expected = date(1975, 05, 07)
        self.assertEqual(value, expected)


    def test_date_encode(self):
        data = date(1975, 05, 07)
        value = ISOCalendarDate.encode(data)
        expected = '1975-05-07'
        self.assertEqual(value, expected)


class ISODateTimeTestCase(TestCase):

    def test_datetime_decode(self):
        test_dates = {
            '1975-05-07T00:15':    (1975, 5, 7, 0,15),
            '1969-07-21T02:56:15': (1969, 7, 21, 2, 56, 15)}

        for data, result in test_dates.iteritems():
            value =  ISODateTime.decode(data)
            expected = datetime(*result)
            self.assertEqual(value, expected)


    def test_datetime_encode(self):
        test_dates = {
            (1975, 5, 7, 0,15):       '1975-05-07T00:15:00',
            (1969, 7, 21, 2, 56, 15): '1969-07-21T02:56:15'}

        for data, expected in test_dates.iteritems():
            data = datetime(*data)
            value =  ISODateTime.encode(data)
            self.assertEqual(value, expected)


class InternetDateTimeTestCase(TestCase):

    def test_datetime(self):
        test_dates = {
            'Tue, 14 Jun 2005 09:00:00 -0400': '2005-06-14 13:00:00',
            'Tue, 14 Jun 2005 09:00:00 +0200': '2005-06-14 07:00:00',
            'Thu, 28 Jul 2005 15:36:55 EDT': '2005-07-28 19:36:55',
            'Fri, 29 Jul 2005 05:50:13 GMT': '2005-07-29 05:50:13',
            '29 Jul 2005 07:27:19 UTC': '2005-07-29 07:27:19',
            '02 Jul 2005 09:52:23 GMT': '2005-07-02 09:52:23'
        }
        for dt, utc in test_dates.items():
            d = InternetDateTime.decode(dt)
            self.assertEqual(InternetDateTime.encode(d), utc)


class XMLTestCase(TestCase):
    data  = """<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">""" \
            """Astérix le Gaulois</dc:title>"""
    result1 = """&lt;dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">""" \
            """Astérix le Gaulois&lt;/dc:title>"""
    result2 = """&lt;dc:title xmlns:dc=&quot;http://purl.org/dc/elements/""" \
              """1.1/&quot;>Astérix le Gaulois&lt;/dc:title>"""

    def test_encode(self):
        self.assertEqual(XML.encode(self.data), self.result1)
        self.assertEqual(XMLAttribute.encode(self.data), self.result2)

    def test_decode(self):
        self.assertEqual(XML.decode(self.result1), self.data)
        self.assertEqual(XMLAttribute.decode(self.result2), self.data)



class LanguageTagTestCase(TestCase):
    """TODO with an example"""



if __name__ == '__main__':
    unittest.main()
