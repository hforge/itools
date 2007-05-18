# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import logging
import sys
import warnings

# Import from itools
from itools.datatypes import Unicode, XMLAttribute
from itools.schemas import get_datatype_by_uri
from itools.handlers import Text, register_handler_class
from i18n import Translatable
from namespaces import get_namespace, is_empty, XMLNSNamespace
from parser import (Parser, XML_DECL, DOCUMENT_TYPE, START_ELEMENT,
                    END_ELEMENT, TEXT, COMMENT)


#############################################################################
# Data types
#############################################################################

# Serialize
def get_qname(ns_uri, name):
    """Returns the fully qualified name"""
    if ns_uri is None:
        return name
    prefix = get_namespace(ns_uri).class_prefix
    if prefix is None:
        return name
    return '%s:%s' % (prefix, name)


def get_attribute_qname(namespace, local_name):
    """Returns the fully qualified name"""
    if namespace is None:
        return local_name

    prefix = get_namespace(namespace).class_prefix
    if prefix is None:
        return local_name

    # Namespace declarations for the default namespace lack the local
    # name (e.g. xmlns="http://www.example.org"). Here 'xmlns' is always
    # the prefix, and there is not a local name. This an special case.
    if local_name is None:
        return prefix

    return '%s:%s' % (prefix, local_name)


def get_start_tag(tag_uri, tag_name, attributes):
    s = '<%s' % get_qname(tag_uri, tag_name)
    # Output the attributes
    for attr_uri, attr_name in attributes:
        value = attributes[(attr_uri, attr_name)]
        qname = get_attribute_qname(attr_uri, attr_name)
        datatype = get_datatype_by_uri(attr_uri, attr_name)
        value = datatype.encode(value)
        value = XMLAttribute.encode(value)
        s += ' %s="%s"' % (qname, value)
    # Close the start tag
    if is_empty(tag_uri, tag_name):
        return s + '/>'
    else:
        return s + '>'


def get_end_tag(ns_uri, name):
    if is_empty(ns_uri, name):
        return ''
    return '</%s>' % get_qname(ns_uri, name)


def stream_to_str(stream, encoding='UTF-8'):
    data = []
    for event, value in stream:
        if event == TEXT:
            value = value.encode(encoding)
            data.append(value)
        elif event == START_ELEMENT:
            ns_uri, name, attributes = value
            data.append(get_start_tag(ns_uri, name, attributes))
        elif event == END_ELEMENT:
            ns_uri, name = value
            data.append(get_end_tag(ns_uri, name))
        elif event == COMMENT:
            value = value.encode(encoding)
            data.append('<!--%s-->' % value)
        else:
            raise NotImplementedError, 'unknown event "%s"' % event
    return ''.join(data)



class Element(object):

    __slots__ = ['document', 'start', 'end']

    def __init__(self, document, start):
        self.document = document
        self.start = start
        self.end = document.find_end(start)


    def get_content_elements(self):
        events = self.document.events

        i = self.start + 1
        while i < self.end:
            yield events[i]
            i += 1


    def get_content(self, encoding='UTF-8'):
        return stream_to_str(self.get_content_elements())


    def get_content_as_html(self, encoding='UTF-8'):
        from itools.xhtml import stream_to_str_as_html
        return stream_to_str_as_html(self.get_content_elements())




#############################################################################
# Documents
#############################################################################
class Document(Translatable, Text):
    """
    An XML file is represented in memory as a tree where the nodes are
    instances of the classes 'Element' and 'Raw'. The 'Element' class
    represents an XML element, the 'Raw' class represents a text string.

    XML sub-classes will, usually, provide their specific semantics by
    providing their own Element and Raw classes. This is the reason why
    we use 'self.Element' and 'self.Raw' throghout the code instead of
    just 'Element' and 'Raw'.
    """

    class_mimetypes = ['text/xml', 'application/xml']
    class_extension = 'xml'


    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'document_type', 'events']


    def new(self):
        # XML is a meta-language, it does not make change to create a bare
        # XML handler without a resource.
        raise NotImplementedError


    def _load_state_from_file(self, file):
        """
        Builds a tree made of elements and raw data.
        """
        xmlns_uri = XMLNSNamespace.class_uri
        # Default values
        self.document_type = None
        # Parse
        events = []
        for event, value, line_number in Parser(file.read()):
            if event == DOCUMENT_TYPE:
                self.document_type = value
            elif event == TEXT or event == COMMENT:
                # XXX The encoding is hard-coded, should it be?
                value = unicode(value, 'UTF-8')
                events.append((event, value))
            elif event == XML_DECL:
                pass
            else:
                events.append((event, value))

        self.events = events


    #######################################################################
    # API
    #######################################################################
    def header_to_str(self, encoding='UTF-8'):
        s = []
        # The XML declaration
        s.append('<?xml version="1.0" encoding="%s"?>\n' % encoding)
        # The document type
        if self.document_type is not None:
            pattern = '<!DOCTYPE %s\n' \
                      '     PUBLIC "%s"\n' \
                      '    "%s">\n'
            s.append(pattern % self.document_type[:3])

        return ''.join(s)


    def to_str(self, encoding='UTF-8'):
        data = [self.header_to_str(encoding)]
        data.append(stream_to_str(self.events, encoding))

        return ''.join(data)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.__dict__, other.__dict__)


    def find_end(self, start):
        c = 1
        i = start + 1
        while c:
            event, value = self.events[i]
            if event == START_ELEMENT:
                c += 1
            elif event == END_ELEMENT:
                c -= 1
            i = i + 1
        return i


    def get_element(self, name):
        i = 0
        for event, value in self.events:
            if event == START_ELEMENT:
                if name == value[1]:
                    return Element(self, i)
            i += 1
        return None


    def to_text(self):
        """
        Removes the markup and returns a plain text string.
        """
        text = [ value for event, value in self.events if event == TEXT ]
        return u' '.join(text)


register_handler_class(Document)
