# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2002, 2003 J. David Ibáñez <jdavid@itaapy.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Python
from sets import Set
import unittest
from unittest import TestCase

# Import from itools.handlers
from PO import PO



class POTestCase(TestCase):
    def test_case1(self):
        """Test for newlines."""
        content = 'msgid "Add"\n' \
                  'msgstr "Añadir\\n"\n'

        po = PO(content)
        assert po.messages == {('Add',): ([], [u'Añadir\n'])}


    def test_case2(self):
        """Test for multiple lines"""
        content = 'msgid "Hello world"\n' \
                  'msgstr ""\n' \
                  '"Hola "\n' \
                  '"mundo"\n'

        po = PO(content)
        assert po.messages == {('Hello world',): ([], ['', 'Hola ', 'mundo'])}


    def test_case3(self):
        """Test for double quotes."""
        content = 'msgid "test"\n' \
                  'msgstr "Esto es una \\"prueba\\""\n'

        po = PO(content)
        assert po.messages == {('test',): ([], ['Esto es una "prueba"'])}


    def test_output(self):
        """Test output"""
        content = '# Comment\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'

        po = PO(content)
        assert po.get_data() == content


if __name__ == '__main__':
    unittest.main()
