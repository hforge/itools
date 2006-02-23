# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas Oyez <noyez@itaapy.com>
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
from itools.resources import get_resource
from XLIFF import XLIFF


src = get_resource('gettext_en_es.xlf')


class TMXTestCase(TestCase):

    def test_input(self):
        """Test input."""
        xliff = XLIFF(src)
        open('test.xlf', 'w').write(xliff.to_str())

 
if __name__ == '__main__':
    unittest.main()
