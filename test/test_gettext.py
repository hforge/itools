# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2006 J. David Ibáñez <jdavid@itaapy.com>
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
from itools.gettext import PO



class POTestCase(TestCase):

    def test_case1(self):
        """Test for newlines."""
        content = 'msgid "Add"\n' \
                  'msgstr "Ajouter\\n"\n'
        po = PO()
        po.load_state_from_string(content)

        self.assertEqual(po.get_msgstr('Add'), u'Ajouter\n')


    def test_case2(self):
        """Test for multiple lines."""
        content = 'msgid "Hello world"\n' \
                  'msgstr ""\n' \
                  '"Hola "\n' \
                  '"mundo"\n'
        po = PO()
        po.load_state_from_string(content)

        self.assertEqual(po.get_msgstr('Hello world'), u'Hola mundo')


    def test_case3(self):
        """Test for double quotes."""
        content = 'msgid "test"\n' \
                  'msgstr "Esto es una \\"prueba\\""\n'
        po = PO()
        po.load_state_from_string(content)

        self.assertEqual(po.get_msgstr('test'), u'Esto es una "prueba"')


    def test_output(self):
        """Test output."""
        content = '# Comment\n' \
                  '#: pouet.py:45\n' \
                  '#, fuzzy\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'
        po = PO()
        po.load_state_from_string(content)

        self.assertEqual((po.get_messages())[0].to_str(), content)

        
    def test_fuzzy(self):
        """Test fuzzy."""
        content = '# Comment\n' \
                  '#: pouet.py:45\n' \
                  '#, fuzzy\n' \
                  'msgid "Hello"\n' \
                  'msgstr ""\n' \
                  '"Hola\\n"\n'
        po = PO()
        po.load_state_from_string(content)

        translation = po.gettext('Hello')
        self.assertEqual(translation, 'Hello')


    def test_end_comment(self):
        """Test end comment."""
        content = '#, fuzzy\n' \
                  '#~ msgid "Hello"\n' \
                  '#~ msgstr "Hola"\n'
        po = PO()
        po.load_state_from_string(content)

        translation = po.gettext('Hello')
        self.assertEqual(translation,'Hello')



if __name__ == '__main__':
    unittest.main()
