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
from itools.datatypes import Unicode, XML as XMLContent, XMLAttribute
from itools.schemas import get_datatype_by_uri
from itools.handlers import Text, register_handler_class
from exceptions import XMLError
from namespaces import get_namespace, is_empty, XMLNSNamespace
from parser import (Parser, XML_DECL, DOCUMENT_TYPE, START_ELEMENT,
                    END_ELEMENT, TEXT, COMMENT)


#############################################################################
# Data types
#############################################################################

# Streams
def filter_root_stream(root):
    for event, node in root.traverse():
        if node is not root:
            yield event, node


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


def get_start_tag(ns_uri, name, attributes):
    s = '<%s' % get_qname(ns_uri, name)
    # Output the attributes
    for namespace_uri, local_name in attributes:
        value = attributes[(namespace_uri, local_name)]
        qname = get_attribute_qname(namespace_uri, local_name)
        type = get_datatype_by_uri(namespace_uri, local_name)
        value = type.encode(value)
        value = XMLAttribute.encode(value)
        s += ' %s="%s"' % (qname, value)
    # Close the start tag
    if is_empty(ns_uri, name):
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


# API
def element_to_str(element, encoding='UTF-8'):
    return stream_to_str(element.traverse(), encoding)


def element_content_to_str(element, encoding='UTF-8'):
    return stream_to_str(filter_root_stream(element), encoding)



class Element(object):

    __slots__ = ['namespace', 'name', 'attributes', 'end_tag']


    def __init__(self, namespace, name, attributes=None):
        self.namespace = namespace
        self.name = name
        # Attributes (including namespace declarations)
        if attributes is None:
            self.attributes = {}
        else:
            self.attributes = attributes
        # End tag
        self.end_tag = None


    #######################################################################
    # API
    #######################################################################
    def copy(self):
        """
        DOM: cloneNode.
        """
        # Build a new node
        clone = self.__class__(self.name)
        # Copy the attributes
        clone.attributes = self.attributes.copy()
        # Copy the children
        for child in self.children:
            if isinstance(child, unicode):
                self.children.append(child)
            else:
                self.children.append(child.copy())
        return clone


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if self.name == other.name:
            if set(self.get_attributes()) == set(other.get_attributes()):
                if self.children == other.children:
                    return 0
            return 0
        return 1


    #######################################################################
    # Serialization
    def get_content(self, encoding='UTF-8'):
        s = []
        for node in self.children:
            if isinstance(node, unicode):
                node = node.encode(encoding)
                s.append(XMLContent.encode(node))
            else:
                s.append(node.to_str(encoding=encoding))
        return ''.join(s)


    def to_unicode(self):
        # Used today only by 'itools.i18n.segment' (XHTML translation)
        return unicode(element_to_str(self), 'utf-8')


    #######################################################################
    # Attributes
    def set_attribute(self, namespace, name, value):
        self.attributes[(namespace, name)] = value


    def get_attribute(self, namespace, local_name):
        return self.attributes[(namespace, local_name)]


    def has_attribute(self, namespace, local_name):
        return (namespace, local_name) in self.attributes


    def get_attributes(self):
        for key, value in self.attributes.items():
            yield key[0], key[1], value


    #######################################################################
    # Children
    def set_comment(self, comment):
        self.children.append(comment)


    def set_element(self, element):
        self.children.append(element)


    def set_text(self, text, encoding='UTF-8'):
        text = Unicode.decode(text, encoding)
        children = self.children
        if children and isinstance(children[-1], unicode):
            children[-1] = children[-1] + text
        else:
            children.append(text)


    def get_elements(self, name=None):
        elements = []
        for x in self.children:
            if isinstance(x, Element) and (name is None or x.name == name):
                elements.append(x)
        return elements





#############################################################################
# Documents
#############################################################################
class Document(Text):
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


    #######################################################################
    # The Document Types registry
    #######################################################################
    doctype_handlers = {}


    @classmethod
    def set_doctype_handler(cls, public_id, handler):
        cls.doctype_handlers[public_id] = handler


    @classmethod
    def get_doctype_handler(cls, public_id):
        return cls.doctype_handlers.get(public_id)


    @classmethod
    def has_doctype_handler(cls, public_id):
        return public_id in cls.doctype_handlers


    #######################################################################
    # Load
    #######################################################################

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


    def get_element(self, name):
        for event, value in self.events:
            if event == START_ELEMENT:
                if name == value[1]:
                    # TODO Should return something else
                    return value
        return None


    def traverse(self):
        skip = 0
        for event, value in self.events:
            if skip:
                if event == START_ELEMENT:
                    skip += 1
                elif event == END_ELEMENT:
                    skip -= 1
            if skip:
                continue

            command = yield event, value
            if command == 1:
                skip = 1


    def to_text(self):
        """
        Removes the markup and returns a plain text string.
        """
        text = []
        for event, node in self.traverse():
            if event == TEXT:
                text.append(node)
        return u' '.join(text)


register_handler_class(Document)


#############################################################################
# XML Factory
#############################################################################
def guess_doctype(resource):
    resource.open()
    data = resource.read()
    resource.close()
    for event, value, line_number in Parser(data):
        if event == DOCUMENT_TYPE:
            return value
        elif event == START_ELEMENT:
            return None
    return None


##def get_handler(resource):
##    """
##    Factory for XML handlers. From a given resource, try to guess its document
##    type, and return the proper XML handler.
##    """
##    doctype = guess_doctype(resource)
##    if registry.has_doctype(doctype):
##        handler_class = registry.get_doctype(doctype)
##    else:
##        handler_class = Document
##    return handler_class(resource)
