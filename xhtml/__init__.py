# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import mimetypes

# Import from itools
from xhtml import (xhtml_uri, Document, stream_to_str_as_html,
                   stream_to_str_as_xhtml, elements_schema)


__all__ = [
    'xhtml_uri',
    'Document',
    'elements_schema',
    # New API (work in progress)
    'stream_to_str_as_html',
    'stream_to_str_as_xhtml']


mimetypes.add_type('application/xhtml+xml', '.xhtml')
