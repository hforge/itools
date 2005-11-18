# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


# Import from Python
import unittest
from unittest import TestCase

# Import from itools
from __init__ import get_resource
import file
import http


class FileTestCase(TestCase):
    def setUp(self):
        self.tests = get_resource('tests')


    def test_has_resource(self):
        assert self.tests.has_resource('index.html.en') is True


    def test_has_not_resource(self):
        assert self.tests.has_resource('index.html.es') is False


    def test_link(self):
        c = self.tests.get_resource('c')
        tests = c.get_resource('..')
        assert 'c' in tests.get_resource_names()


##    def test_python(self):
##        resource = get_resource('base.py')
##        assert resource.get_mimetype() == 'text/x-python'


##    def test_html(self):
##        resource = get_resource('tests/index.html.en')
##        assert resource.get_mimetype() == 'text/html'


##    def test_folder(self):
##        folder = get_resource('tests')
##        assert folder.get_mimetype() == 'application/x-not-regular-file'







if __name__ == '__main__':
    unittest.main()
