# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from Python
import unittest
from unittest import TestCase

# Import from itools.handlers
from Var import Var


data = """\
URI: upgrading.html.de
Content-Language: de
Content-type: text/html; charset=ISO-8859-1

URI: upgrading.html.en
Content-Language: en
Content-type: text/html; charset=ISO-8859-1

URI: upgrading.html.fr
Content-Language: fr
Content-type: text/html; charset=ISO-8859-1
"""



class VarTestCase(TestCase):
    def setUp(self):
        self.var = Var(data)


    def test_nrecords(self):
        assert len(self.var.records) == 3


    def test_uri(self):
        assert self.var.records[0].uri == 'upgrading.html.de'


    def test_type(self):
        assert self.var.records[0].type == 'text/html; charset=ISO-8859-1'


    def test_language(self):
        assert self.var.records[0].language == 'de'



if __name__ == '__main__':
    unittest.main()
