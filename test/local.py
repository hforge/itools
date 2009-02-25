# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

"""Import this module to test the local itools, so you don't need to
reinstall itools after each modification.

In every 'test_*.py' file, import 'local' before importing anything from
itools:

  # Import from itools
  import local
  from itools import ...
"""

# Import from the Standard Library
from imp import load_module, PKG_DIRECTORY
from os import getcwd
from os.path import dirname


# Load the local itools
path = getcwd()      # The test folder
path = dirname(path) # The itools folder
load_module('itools', None, path, ('', '', PKG_DIRECTORY))

