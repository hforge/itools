# -*- coding: UTF-8 -*-
# Copyright (C) 2002-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
import dublin_core
from exceptions import XMLError
from namespaces import (XMLNamespace, XMLNSNamespace, get_namespace,
                        get_element_schema, AbstractNamespace, set_namespace)
from parser import (Parser, XML_DECL, DOCUMENT_TYPE, START_ELEMENT,
                    END_ELEMENT, TEXT, COMMENT, PI, CDATA)
from xml import (Document, Element, Comment,
                 filter_root_stream, element_to_str, element_content_to_str,
                 Context)
from indexer import xml_to_text
from office import (MSWord, MSExcel, MSPowerPoint, OOWriter, OOCalc,
                    OOImpress, PDF)



__all__ = [
    # New API (in progress)
    'filter_root_stream',
    'element_to_str',
    'element_content_to_str',
    'Context',
    # Exceptions
    'XMLError',
    # Namespaces
    'XMLNamespace',
    'XMLNSNamespace',
    'get_namespace',
    'get_element_schema',
    'AbstractNamespace',
    'set_namespace',
    # Parsing
    'Parser',
    'XML_DECL',
    'DOCUMENT_TYPE',
    'START_ELEMENT',
    'END_ELEMENT',
    'TEXT',
    'COMMENT',
    'PI',
    'CDATA',
    # Handlers
    'Document',
    'Element',
    'Comment',
    # Office
    'MSWord',
    'MSExcel',
    'MSPowerPoint',
    'OOWriter',
    'OOCalc',
    'OOImpress',
    'PDF',
    # Functions
    'xml_to_text',
]
