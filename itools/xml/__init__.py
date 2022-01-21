# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from itools.xml import dublin_core
from .namespaces import XMLNamespace, xml_uri, xmlns_uri
from .namespaces import register_namespace, get_namespace, has_namespace
from .namespaces import ElementSchema, get_element_schema, get_attr_datatype
from .namespaces import is_empty
from parser import XMLParser, DocType, register_dtd, XMLError, XML_DECL
from parser import DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT, COMMENT
from parser import PI, CDATA
from .utils import is_xml_stream, xml_to_text
from .xml import Element, stream_to_str, get_element, find_end
from .xml import get_qname, get_attribute_qname, get_end_tag, get_doctype


__all__ = [
    # New API (in progress)
    'get_qname',
    'get_attribute_qname',
    'get_end_tag',
    'get_doctype',
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
    'has_namespace',
    'get_element_schema',
    'get_attr_datatype',
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
    # DocType
    'DocType',
    # Handlers
    'Element',
    # Functions
    'register_dtd',
    'is_xml_stream',
    'xml_to_text',
]
