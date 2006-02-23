# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import mailto


class MailtoTestCase(unittest.TestCase):

    def setUp(self):
        self.username = 'jdavid'
        self.host = 'itaapy.com'
        self.address = 'jdavid@itaapy.com'
        self.uri = 'mailto:jdavid@itaapy.com'
        self.uri_no_host = 'mailto:jdavid'


    def test_mailto(self):
        """Regular Mailto object."""
        ob = mailto.Mailto(self.username, self.host)
        self.assertEqual(ob.username, self.username)
        self.assertEqual(ob.host, self.host)
        self.assertEqual(str(ob), self.uri)


    def test_mailto_no_host(self):
        """Mailto object with no host."""
        ob = mailto.Mailto(self.username, None)
        self.assertEqual(ob.username, self.username)
        self.assertEqual(ob.host, None)
        self.assertEqual(str(ob), self.uri_no_host)


    def test_decode(self):
        """Decoding of a regular "mailto:" reference."""
        ob = mailto.decode(self.address)
        self.assert_(isinstance(ob, mailto.Mailto))
        self.assertEqual(ob.username, self.username)
        self.assertEqual(ob.host, self.host)
        self.assertEqual(str(ob), self.uri)


    def test_decode_no_host(self):
        """Decoding of a "mailto:" reference with no @host."""
        ob = mailto.decode(self.username)
        self.assert_(isinstance(ob, mailto.Mailto))
        self.assertEqual(ob.username, self.username)
        self.assertEqual(ob.host, None)
        self.assertEqual(str(ob), self.uri_no_host)


    def test_compare(self):
        """Compare two Mailto objects with same parameters."""
        ob = mailto.Mailto(self.username, self.host)
        copy = mailto.decode(self.address)
        self.assert_(type(ob) is type(copy))
        self.assertEqual(ob.username, copy.username)
        self.assertEqual(ob.host, copy.host)
        self.assertEqual(str(ob), str(copy))
        self.assertEqual(ob, copy)



if __name__ == '__main__':
    unittest.main()
