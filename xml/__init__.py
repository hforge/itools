# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
import dublin_core
from namespaces import XMLNamespace, register_namespace, get_namespace
from namespaces import xml_uri, xmlns_uri, get_element_schema, ElementSchema
from namespaces import is_empty
from parser import XMLParser, register_dtd, XMLError, XML_DECL, DOCUMENT_TYPE
from parser import START_ELEMENT, END_ELEMENT, TEXT, COMMENT, PI, CDATA
from xml import XMLFile, Element, stream_to_str, get_element, find_end
from xml import get_qname, get_attribute_qname, get_start_tag, get_end_tag
from indexer import xml_to_text
from office import OfficeDocument, MSWord, MSExcel, MSPowerPoint, RTF
from i18n import translate



__all__ = [
    # New API (in progress)
    'get_qname',
    'get_attribute_qname',
    'get_start_tag',
    'get_end_tag',
    'stream_to_str',
    'find_end',
    'get_element',
    # Exceptions
    'XMLError',
    # Namespaces
    'xml_uri',
    'xmlns_uri',
    'XMLNamespace',
    'register_namespace',
    'get_namespace',
    'get_element_schema',
    'is_empty',
    'ElementSchema',
    # Parsing
    'XMLParser',
    'XML_DECL',
    'DOCUMENT_TYPE',
    'START_ELEMENT',
    'END_ELEMENT',
    'TEXT',
    'COMMENT',
    'PI',
    'CDATA',
    # Handlers
    'XMLFile',
    'Element',
    # Office
    'OfficeDocument',
    'MSWord',
    'MSExcel',
    'MSPowerPoint',
    'RTF',
    # Functions
    'register_dtd',
    'xml_to_text',
    'translate',
]
