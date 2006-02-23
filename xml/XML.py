# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import logging
import sys
import warnings

# Import from itools
from itools.handlers import File, Text
from itools.datatypes import Unicode
from itools import schemas
from itools.schemas import get_datatype_by_uri
from itools.xml.exceptions import XMLError
from itools.xml import namespaces
from itools.xml import parser


#############################################################################
# Data types
#############################################################################

class Comment(object):

    parent = None

    def __init__(self, data):
        self.data = data


    def to_str(self, encoding='UTF-8'):
        return '<!--%s-->' % self.data.encode(encoding)


    def copy(self):
        return Comment(self.data)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.data, other.data)



class Element(object):

    namespace = None


    def __init__(self, name):
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
        prefix = namespaces.get_namespace(self.namespace).class_prefix
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
    def to_str(self, encoding='UTF-8'):
        return self.get_start_tag() \
               + self.get_content(encoding) \
               + self.get_end_tag()


    def get_start_tag(self):
        s = '<%s' % self.qname
        # Output the attributes
        for namespace_uri, local_name, value in self.get_attributes():
            qname = self.get_attribute_qname(namespace_uri, local_name)
            type = get_datatype_by_uri(namespace_uri, local_name)
            value = type.encode(value)
            s += ' %s="%s"' % (qname, value)
        # Close the start tag
        namespace = namespaces.get_namespace(self.namespace)
        schema = namespace.get_element_schema(self.name)
        is_empty = schema.get('is_empty', False)
        if is_empty:
            return s + '/>'
        else:
            return s + '>'


    def get_end_tag(self):
        namespace = namespaces.get_namespace(self.namespace)
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
                # XXX This is equivalent to 'Unicode.encode',
                # there should be a single place.
                s.append(node.replace('&', '&amp;').replace('<', '&lt;'))
            else:
                s.append(node.to_str(encoding=encoding))
        return ''.join(s)


    def to_unicode(self):
        # Used today only by 'itools.i18n.segment' (XHTML translation)
        return unicode(self.to_str(), 'utf-8')


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

        prefix = namespaces.get_namespace(namespace).class_prefix
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
        yield self
        for child in self.children:
            if isinstance(child, Element):
                for x in child.traverse():
                    yield x
            else:
                yield child


    def traverse2(self, context=None):
        if context is None:
            context = Context()
        # Down
        context.start = True
        yield self, context
        # Children
        if context.skip is True:
            context.skip = False
        else:
            for child in self.children:
                if isinstance(child, Element):
                    for x, context in child.traverse2(context):
                        yield x, context
                else:
                    yield child, context
        # Up
        context.start = False
        yield self, context


    #######################################################################
    # Internationalization
    def is_translatable(self, attribute_name=None):
        """
        Some elements may contain text addressed to users, that is, text
        that could be translated in different human languages, for example
        the 'p' element of XHTML. This method should return 'True' in that
        cases, False (the default) otherwise.

        If the parameter 'attribute_name' is given, then we are being asked
        wether that attribute is or not translatable. An example is the 'alt'
        attribute of the 'img' elements of XHTML.
        """
        return False



#############################################################################
# Documents
#############################################################################

class Context(object):
    """Used by 'traverse2' to control the traversal."""

    def __init__(self):
        self.skip = False



class Document(Text.Text):
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
    def _load_state(self, resource):
        """
        Builds a tree made of elements and raw data.
        """
        state = self.state
        # Default values
        state.document_type = None
        xml_namespaces = set()
        # Parse
        stack = []
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.DOCUMENT_TYPE:
                state.document_type = value
            elif event == parser.START_ELEMENT:
                namespace_uri, element_name, attributes = value
                namespace = namespaces.get_namespace(namespace_uri)
                try:
                    schema = namespace.get_element_schema(element_name)
                except XMLError, e:
                    e.line_number = line_number
                    raise e
                element_type = schema['type']
                element = element_type(element_name)
                element.attributes = attributes
                stack.append(element)
            elif event == parser.END_ELEMENT:
                element = stack.pop()
                if stack:
                    stack[-1].set_element(element)
                else:
                    state.root_element = element
            elif event == parser.COMMENT:
                # Comments out of the root element are discarded (XXX)
                if stack:
                    stack[-1].set_comment(Comment(value))
            elif event == parser.TEXT:
                if stack:
                    stack[-1].set_text(value, 'UTF-8')
            elif event == parser.NAMESPACE:
                xml_namespaces.add(value)

        # Add the XML namespaces to the root element
        root_element = state.root_element
        xmlns_uri = namespaces.XMLNSNamespace.class_uri
        for xml_namespace in xml_namespaces:
            prefix = namespaces.get_namespace(xml_namespace).class_prefix
            root_element.set_attribute(xmlns_uri, prefix, xml_namespace)


    #######################################################################
    # API
    #######################################################################
    def header_to_str(self, encoding='UTF-8'):
        state = self.state

        s = []
        # The XML declaration
        s.append('<?xml version="1.0" encoding="%s"?>\n' % encoding)
        # The document type
        if state.document_type is not None:
            pattern = '<!DOCTYPE %s\n' \
                      '     PUBLIC "%s"\n' \
                      '    "%s">\n'
            s.append(pattern % state.document_type[:3])

        return ''.join(s)


    def to_str(self, encoding='UTF-8'):
        data = [self.header_to_str(encoding),
                self.get_root_element().to_str(encoding)]

        return ''.join(data)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.state.__dict__, other.state.__dict__)


    def get_root_element(self):
        """
        Returns the root element (XML documents have one root element).
        """
        return self.state.root_element


    def traverse(self):
        for x in self.get_root_element().traverse():
            yield x


    def traverse2(self, context=None):
        if context is None:
            context = Context()
        # Children
        for x, context in self.get_root_element().traverse2(context):
            yield x, context


    def to_text(self):
        """
        Removes the markup and returns a plain text string.
        """
        text = []
        for node in self.traverse():
            if isinstance(node, unicode):
                text.append(node)
        return u' '.join(text)


Text.Text.register_handler_class(Document)


#############################################################################
# XML Factory
#############################################################################
def guess_doctype(resource):
    resource.open()
    data = resource.read()
    resource.close()
    for event, value, line_number in parser.parse(data):
        if event == parser.DOCUMENT_TYPE:
            return value
        elif event == parser.START_ELEMENT:
            return None
    return None


def get_handler(resource):
    """
    Factory for XML handlers. From a given resource, try to guess its document
    type, and return the proper XML handler.
    """
    doctype = guess_doctype(resource)
    if registry.has_doctype(doctype):
        handler_class = registry.get_doctype(doctype)
    else:
        handler_class = Document
    return handler_class(resource)
