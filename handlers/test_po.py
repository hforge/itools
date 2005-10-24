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

# Import from the Standard Library
import unittest
from unittest import TestCase

# Import from itools.handlers
from PO import PO

# Import from itools.resources
from itools.resources.memory import File as mFile


class POTestCase(TestCase):

    def test_case1(self):
        """Test for newlines."""
        content = 'msgid "Add"\n' \
                  'msgstr "Ajouter\\n"\n'
        da = mFile(content)
        po = PO(da)

        self.assertEqual(po._messages['Add'].msgstr, [u'Ajouter\n'])


    def test_case2(self):
        """Test for multiple lines."""
        content = 'msgid "Hello world"\n' \
                  'msgstr ""\n' \
                  '"Hola "\n' \
                  '"mundo"\n'
        da = mFile(content)
        po = PO(da)

        assert po._messages['Hello world'].msgstr == ['', u'Hola ', u'mundo']


    def test_case3(self):
        """Test for double quotes."""
        content = 'msgid "test"\n' \
                  'msgstr "Esto es una \\"prueba\\""\n'
        da = mFile(content)
        po = PO(da)

        assert po._messages['test'].msgstr == [u'Esto es una "prueba"']


    def test_output(self):
        """Test output."""
        content = '# Comment\n' \
                  '#: pouet.py:45\n' \
                  '#, fuzzy\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'
        da = mFile(content)
        po = PO(da)

        assert (po.get_messages())[0].to_str() == content

        
    def test_fuzzy(self):
        """Test fuzzy."""
        content = '# Comment\n' \
                  '#: pouet.py:45\n' \
                  '#, fuzzy\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'
        da = mFile(content)
        po = PO(da)
        translation = po.get_translation('Hello')

        assert translation == 'Hello'

    def test_end_comment(self):
        """Test end comment."""
        content = '#, fuzzy\n' \
                  '#~ msgid "Hello"\n' \
                  '#~ msgstr "Hola"\n'
        da = mFile(content)
        po = PO(da)
        translation = po.get_translation('Hello')

        assert translation == 'Hello'

if __name__ == '__main__':
    unittest.main()
