# -*- coding: UTF-8 -*-
# Copyright (C) 2007 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2007-2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from time import timezone, mktime
from datetime import time, date, datetime
import unittest
from unittest import TestCase
import random, decimal

# Import from itools
from itools.datatypes import ISOTime, ISOCalendarDate, ISODateTime, HTTPDate
from itools.datatypes import Integer, Decimal, Boolean, Unicode, URI, Email
from itools.datatypes import QName, Tokens, Enumerate
from itools.datatypes import XMLContent, XMLAttribute


def datetime_utc2local(dt):
    """Given a naive datetime object in UTC, return a naive datetime object
    in local time.
    """
    # Transform the datetime object to Unix time.
    parts = dt.utctimetuple()
    timestamp = mktime(parts)
    # Change from UTC to local time. (XXX david: I'm still not sure about the
    # line below.)
    timestamp = timestamp - timezone
    # Transform the Unix time to a naive datetime object.
    return datetime.fromtimestamp(timestamp)



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



class XMLTestCase(TestCase):
    data  = """<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">""" \
            """Astérix le Gaulois</dc:title>"""
    result1 = """&lt;dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">""" \
            """Astérix le Gaulois&lt;/dc:title>"""
    result2 = """&lt;dc:title xmlns:dc=&quot;http://purl.org/dc/elements/""" \
              """1.1/&quot;>Astérix le Gaulois&lt;/dc:title>"""

    def test_encode(self):
        self.assertEqual(XMLContent.encode(self.data), self.result1)
        self.assertEqual(XMLAttribute.encode(self.data), self.result2)

    def test_decode(self):
        self.assertEqual(XMLContent.decode(self.result1), self.data)
        self.assertEqual(XMLAttribute.decode(self.result2), self.data)



class HTTPDateTestCase(TestCase):

    def setUp(self):
        """Nearly all tests use the same date.
        But it needs to be converted from the local time to the universal time
        (UTC).
        """
        # The tested date expressed in UTC
        dt = datetime(2007, 11, 6, 8, 49, 37)
        # To local time
        self.expected = datetime_utc2local(dt)


    def test_rfc1123(self):
        """RFC 1123 is mainly used in HTTP.
        """
        date = 'Tue, 06 Nov 2007 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_rfc1123_variation(self):
        """Variation of RFC-1123, uses full day name.
        (sent by Netscape 4)
        """
        date = 'Tuesday, 06 Nov 2007 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_rfc822(self):
        """RFC 822 is the ancestor of RFC 1123.
        """
        date = 'Tue, 06 Nov 07 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_rfc850(self):
        """RFC 850
        """
        date = 'Tuesday, 06-Nov-07 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_rfc850_variation(self):
        """Variation of RFC-850, uses full month name and full year.
        (unknow sender)
        """
        date = 'Tuesday, 06-November-07 08:49:37 GMT'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_rfc_2822(self):
        """RFC 2822
        """
        date = 'Tue, 06 Nov 2007 10:49:37 +0200'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_timezone(self):
        """CST is GMT-6.
        """
        date = 'Tue, 06 Nov 2007 02:49:37 CST'
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_asctime(self):
        """ANSI C's asctime().
        """
        # Convert to 'Tue Nov  6 09:49:37 2007' in UTC+1
        date = self.expected.ctime()
        date = HTTPDate.decode(date)
        self.assertEqual(date, self.expected)


    def test_encode(self):
        """Convert local time to universal time.
        """
        # November
        dt_utc = datetime(2007, 11, 6, 8, 49, 37)
        expected = 'Tue, 06 Nov 2007 08:49:37 GMT'
        dt_local = datetime_utc2local(dt_utc)
        self.assertEqual(HTTPDate.encode(dt_local), expected)

        # August
        dt_utc = datetime(2007, 8, 6, 8, 49, 37)
        expected = 'Mon, 06 Aug 2007 08:49:37 GMT'
        dt_local = datetime_utc2local(dt_utc)
        self.assertEqual(HTTPDate.encode(dt_local), expected)



class LanguageTagTestCase(TestCase):
    """TODO with an example"""



if __name__ == '__main__':
    unittest.main()
