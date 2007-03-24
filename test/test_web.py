# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from unittest import TestCase

# Import from itools
from itools import vfs
import itools.http
from itools.web import Server, Root



class ServerTestCase(TestCase):
    
    def test00_simple(self):
        class MyRoot(Root):
            GET__access__ = True
            def GET(self, context):
                return 'hello world'
        root = MyRoot()
        server = Server(root)
##        server.start()




if __name__ == '__main__':
    unittest.main()
