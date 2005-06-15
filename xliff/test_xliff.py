# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Nicolas OYEZ <noyez@itaapy.com>
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
import unittest
from unittest import TestCase

# Import from itools.xliff
from XLIFF import XLIFF

# Import from itools.resources
from itools.resources import get_resource

file = "gettext_en_fr.xlf"
#file = "test.xlf"

class TMXTestCase(TestCase):

    def test_input(self):
        """Test input."""
        
        src = get_resource(file)
        xliff = XLIFF(src)
        fd = open('test.xlf', 'w')
        fd.write(xliff.to_str())
        fd.close()

 
if __name__ == '__main__':
    unittest.main()
