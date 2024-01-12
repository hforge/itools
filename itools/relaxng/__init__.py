# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009 J. David Ibáñez <jdavid.ibp@gmail.com>
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

# Import from itools
from itools.core import add_type
from .relaxng import RelaxNGFile

__all__ = [
    'RelaxNGFile',
    ]

# Register type
add_type('text/x-rng', '.rng')

