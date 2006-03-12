# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002, 2003 J. David Ibáñez <jdavid@itaapy.com>
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
from unittest import TestCase

# Import from itools
from itools.i18n.accept import AcceptLanguage

# Import from itools.handlers
from utils import get_handler


class BasicTestCase(TestCase):
    def test_get(self):
        handler = get_handler('../examples/hello.txt.en')
        assert handler.serialize() == 'hello world\n'


    def test_lang(self):
        accept = AcceptLanguage('es')
        handler = get_handler('../examples/hello.txt')
        assert handler.serialize() == 'hola mundo\n'


if __name__ == '__main__':
    unittest.main()
