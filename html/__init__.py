# -*- coding: UTF-8 -*-
# Copyright (C) 2006-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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
from mimetypes import add_type

# Import from itools
from itools.utils import get_abspath
from itools.xml import register_dtd
from html import HTMLFile
from parser import HTMLParser
from xhtml import XHTMLFile, xhtml_uri
from xhtml import stream_to_str_as_html, stream_to_str_as_xhtml
from xhtml import sanitize_stream, sanitize_str
import schema


# Public API
__all__ = [
    # File Handlers
    'XHTMLFile',
    'HTMLFile',
    # Parsers
    'HTMLParser',
    # Functions
    'stream_to_str_as_html',
    'stream_to_str_as_xhtml',
    'sanitize_stream',
    'sanitize_str',
    # Constants
    'xhtml_uri',
    ]


# Register type
add_type('application/xhtml+xml', '.xhtml')

# Register DTD
# -//W3C//DTD XHTML 1.0 Strict//EN
register_dtd('urn:publicid:-:W3C:DTD+XHTML+1.0+Strict:EN',
             get_abspath('xhtml1-strict.dtd'))

#-//W3C//DTD XHTML 1.0 Transitional//EN
register_dtd('urn:publicid:-:W3C:DTD+XHTML+1.0+Transitional:EN',
             get_abspath('xhtml1-transitional.dtd'))

# -//W3C//DTD XHTML 1.0 Frameset//EN
register_dtd('urn:publicid:-:W3C:DTD+XHTML+1.0+Frameset:EN',
             get_abspath('xhtml1-frameset.dtd'))

# -//W3C//ENTITIES Latin 1 for XHTML//EN
register_dtd('urn:publicid:-:W3C:ENTITIES+Latin+1+for+XHTML:EN',
             get_abspath('xhtml-lat1.ent'))

# -//W3C//ENTITIES Symbols for XHTML//EN
register_dtd('urn:publicid:-:W3C:ENTITIES+Symbols+for+XHTML:EN',
             get_abspath('xhtml-symbol.ent'))

# -//W3C//ENTITIES Special for XHTML//EN
register_dtd('urn:publicid:-:W3C:ENTITIES+Special+for+XHTML:EN',
             get_abspath('xhtml-special.ent'))

