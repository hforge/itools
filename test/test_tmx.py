# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Nicolas Oyez <nicoyez@gmail.com>
# Copyright (C) 2005-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
from unittest import TestCase, main

# Import from itools
from itools.tmx import TMXFile


class TMXTestCase(TestCase):

    def test_input(self):
        """Test input.
        """
        tmx = TMXFile('tests/localizermsgs.tmx')
        tmx.to_str()



if __name__ == '__main__':
    main()
