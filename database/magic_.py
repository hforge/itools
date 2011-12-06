# -*- coding: UTF-8 -*-
# Copyright (C) 2011 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from other libraries
import magic

try:
    magic_open = magic.open
except AttributeError:
    # http://pypi.python.org/pypi/python-magic
    magic_open = magic.magic_open
    mime = magic.Magic(mime=True)
    magic_from_file = mime.from_file
    magic_from_buffer = mime.from_buffer
else:
    # http://www.darwinsys.com/file/
    mime = magic_open(magic.MIME_TYPE)
    mime.load()
    magic_from_file = mime.file
    magic_from_buffer = mime.buffer
