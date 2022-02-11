# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2009 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008-2009 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2010 Henry Obein <henry.obein@gmail.com>
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
from itools.core import add_type, get_abspath
from itools.xml import register_dtd, DocType
from . import schema
from .filters import sanitize_stream, sanitize_str
from .html import HTMLFile
from .parser import HTMLParser
from .xhtml import XHTMLFile, xhtml_uri, stream_is_empty
from .xhtml import stream_to_str_as_html, stream_to_str_as_xhtml


# Public API
__all__ = [
    # File Handlers
    'XHTMLFile',
    'HTMLFile',
    # Parsers
    'HTMLParser',
    # Filters
    'sanitize_stream',
    'sanitize_str',
    # Other functions
    'stream_is_empty',
    'stream_to_str_as_html',
    'stream_to_str_as_xhtml',
    # Constants
    'xhtml_uri',
    'xhtml_doctype',
    ]


# Register type
add_type('application/xhtml+xml', '.xhtml')

# Register DTD
# -//W3C//DTD XHTML 1.0 Strict//EN
register_dtd(get_abspath('xhtml1-strict.dtd'),
             urn='urn:publicid:-:W3C:DTD+XHTML+1.0+Strict:EN')

#-//W3C//DTD XHTML 1.0 Transitional//EN
register_dtd(get_abspath('xhtml1-transitional.dtd'),
             urn='urn:publicid:-:W3C:DTD+XHTML+1.0+Transitional:EN')

# -//W3C//DTD XHTML 1.0 Frameset//EN
register_dtd(get_abspath('xhtml1-frameset.dtd'),
             urn='urn:publicid:-:W3C:DTD+XHTML+1.0+Frameset:EN')

# -//W3C//ENTITIES Latin 1 for XHTML//EN
register_dtd(get_abspath('xhtml-lat1.ent'),
             urn='urn:publicid:-:W3C:ENTITIES+Latin+1+for+XHTML:EN')

# -//W3C//ENTITIES Symbols for XHTML//EN
register_dtd(get_abspath('xhtml-symbol.ent'),
             urn='urn:publicid:-:W3C:ENTITIES+Symbols+for+XHTML:EN')

# -//W3C//ENTITIES Special for XHTML//EN
register_dtd(get_abspath('xhtml-special.ent'),
             urn='urn:publicid:-:W3C:ENTITIES+Special+for+XHTML:EN')

# -//W3C//DTD HTML 4.01//EN
register_dtd(get_abspath('html4.01-strict.dtd'),
             urn='urn:publicid:-:W3C:DTD+HTML+4.01:EN')

# -//W3C//ENTITIES Latin 1//EN//HTML
register_dtd(get_abspath('html-lat1.ent'),
             urn='urn:publicid:-:W3C:ENTITIES+Latin1:EN:HTML')

# -//W3C//ENTITIES Symbols//EN//HTML
register_dtd(get_abspath('html-symbol.ent'),
             urn='urn:publicid:-:W3C:ENTITIES+Symbols:EN:HTML')

# -//W3C//ENTITIES Special//EN//HTML
register_dtd(get_abspath('html-special.ent'),
             urn='urn:publicid:-:W3C:ENTITIES+Special:EN:HTML')

xhtml_doctype = DocType(
    '-//W3C//DTD XHTML 1.0 Strict//EN',
    'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd')

