# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import mimetypes

# Import from itools
from xhtml import (xhtml_uri, Document, stream_to_str_as_html,
                   element_content_to_html)


__all__ = [
    'xhtml_uri',
    'Document',
    # New API (work in progress)
    'stream_to_str_as_html',
    'element_content_to_html']


mimetypes.add_type('application/xhtml+xml', '.xhtml')
