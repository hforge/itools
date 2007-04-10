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
from namespaces import get_namespace, XMLNSNamespace
from parser import (Parser, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT,
                    COMMENT)


#############################################################################
# Data types
#############################################################################

class Comment(object):

    __slots__ = ['data']


    def __init__(self, data):
        self.data = data


    def to_str(self, encoding='UTF-8'):
        return '<!--%s-->' % self.data.encode(encoding)


    def copy(self):
        return Comment(self.data)


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.data == other.data
        return False


    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return self.data != other.data
        return True


# Strams
def filter_root_stream(root):
    for event, node in root.traverse():
        if node is not root:
            yield event, node


# Serialize
def stream_to_str(stream, encoding='UTF-8'):
    data = []
    for event, node in stream:
        if event == TEXT:
            node = node.encode(encoding)
            data.append(node)
        elif event == START_ELEMENT:
            data.append(node.get_start_tag())
        elif event == END_ELEMENT:
            data.append(node.get_end_tag())
        elif event == COMMENT:
            node = node.data
            node = node.encode(encoding)
            data.append('<!--%s-->' % node)
        else:
            raise NotImplementedError, 'unknown event "%s"' % event
    return ''.join(data)


# API
def element_to_str(element, encoding='UTF-8'):
    return stream_to_str(element.traverse(), encoding)


def element_content_to_str(element, encoding='UTF-8'):
    return stream_to_str(filter_root_stream(element), encoding)



class Element(object):

    __slots__ = ['namespace', 'name', 'attributes', 'children']


    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name
        # Attributes (including namespace declarations)
        self.attributes = {}
        # Child nodes
        self.children = []


    #######################################################################
    # API
    #######################################################################
    def get_qname(self):
        """Returns the fully qualified name"""
        if self.namespace is None:
            return self.name
        prefix = get_namespace(self.namespace).class_prefix
        if prefix is None:
            return self.name
        return '%s:%s' % (prefix, self.name)

    qname = property(get_qname, None, None, '')


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
    def get_start_tag(self):
        s = '<%s' % self.qname
        # Output the attributes
        for namespace_uri, local_name, value in self.get_attributes():
            qname = self.get_attribute_qname(namespace_uri, local_name)
            type = get_datatype_by_uri(namespace_uri, local_name)
            value = type.encode(value)
            value = XMLAttribute.encode(value)
            s += ' %s="%s"' % (qname, value)
        # Close the start tag
        namespace = get_namespace(self.namespace)
        schema = namespace.get_element_schema(self.name)
        is_empty = schema.get('is_empty', False)
        if is_empty:
            return s + '/>'
        else:
            return s + '>'


    def get_end_tag(self):
        namespace = get_namespace(self.namespace)
        schema = namespace.get_element_schema(self.name)
        is_empty = schema.get('is_empty', False)
        if is_empty:
            return ''
        return '</%s>' % self.qname


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


    def get_attribute_qname(self, namespace, local_name):
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


    #######################################################################
    # Traverse
    def traverse(self):
        stack = [(END_ELEMENT, self), (START_ELEMENT, self)]
        while stack:
            event, node = stack.pop()
            command = yield event, node
            if event == START_ELEMENT:
                if command == 1:
                    yield END_ELEMENT, node
                    continue
                for child in reversed(node.children):
                    if isinstance(child, unicode):
                        stack.append((TEXT, child))
                    elif isinstance(child, Comment):
                        stack.append((COMMENT, child))
                    elif isinstance(child, Element):
                        stack.append((END_ELEMENT, child))
                        stack.append((START_ELEMENT, child))



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
                 'document_type', 'root_element']


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
        stack = []
        for event, value, line_number in Parser(file.read()):
            if event == DOCUMENT_TYPE:
                self.document_type = value
            elif event == START_ELEMENT:
                namespace_uri, element_name, attributes = value
                # Check the element is defined by the namespace
                # XXX Maybe we should not be so strict.
                namespace = get_namespace(namespace_uri)
                try:
                    namespace.get_element_schema(element_name)
                except XMLError, e:
                    e.line_number = line_number
                    raise e

                element = Element(namespace_uri, element_name)
                element.attributes = attributes
                stack.append(element)
            elif event == END_ELEMENT:
                element = stack.pop()
                if stack:
                    stack[-1].set_element(element)
                else:
                    self.root_element = element
            elif event == COMMENT:
                # Comments out of the root element are discarded (XXX)
                if stack:
                    value = Unicode.decode(value, 'UTF-8')
                    stack[-1].set_comment(Comment(value))
            elif event == TEXT:
                if stack:
                    stack[-1].set_text(value, 'UTF-8')


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
        root = self.get_root_element()
        data = [self.header_to_str(encoding),
                element_to_str(root, encoding)]

        return ''.join(data)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.__dict__, other.__dict__)


    def get_root_element(self):
        """
        Returns the root element (XML documents have one root element).
        """
        return self.root_element


    def traverse(self):
        return self.get_root_element().traverse()


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
