# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import logging
from sets import Set
import sys
import warnings

# Import from itools
from itools.handlers import File, Text
from itools import types
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


    def to_unicode(self, encoding='UTF-8'):
        return u'<!--%s-->' % self.data


    def copy(self):
        return Comment(self.data)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.data, other.data)



class Element(object):

    namespace = None


    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name
        # Attributes (including namespace declarations)
        self.attributes = {}
        self.prefixes = {}
        # Child nodes
        self.children = []


    #######################################################################
    # API
    #######################################################################
    def get_qname(self):
        """Returns the fully qualified name"""
        # Returns attribute's qname
        if self.prefix is None:
            return self.name
        return '%s:%s' % (self.prefix, self.name)

    qname = property(get_qname, None, None, '')


    def copy(self):
        """
        DOM: cloneNode.
        """
        # Build a new node
        clone = self.__class__(self.prefix, self.name)
        # Copy the attributes
        clone.attributes = self.attributes.copy()
        clone.prefixes = self.prefixes.copy()
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
        if self.prefix == other.prefix and self.name == other.name:
            if Set(self.get_attributes()) == Set(other.get_attributes()):
                if self.children == other.children:
                    return 0
            return 0
        return 1


    #######################################################################
    # Serialization
    def to_unicode(self, encoding='UTF-8'):
        return self.get_start_tag() \
               + self.get_content(encoding) \
               + self.get_end_tag()


    def get_start_tag(self):
        s = '<%s' % self.qname
        # Output the attributes
        for namespace_uri, local_name, value in self.get_attributes():
            qname = self.get_attribute_qname(namespace_uri, local_name)
            type = self.get_attribute_type(namespace_uri, local_name)
            value = type.to_unicode(value)
            s += ' %s="%s"' % (qname, value)
        # Close the start tag
        namespace = namespaces.get_namespace(self.namespace)
        schema = namespace.get_element_schema(self.name)
        is_empty = schema.get('is_empty', False)
        if is_empty:
            return s + u'/>'
        else:
            return s + u'>'


    def get_end_tag(self):
        namespace = namespaces.get_namespace(self.namespace)
        schema = namespace.get_element_schema(self.name)
        is_empty = schema.get('is_empty', False)
        if is_empty:
            return u''
        return u'</%s>' % self.qname


    def get_content(self, encoding='UTF-8'):
        s = []
        for node in self.children:
            if isinstance(node, unicode):
                # XXX This is equivalent to 'types.Unicode.to_unicode',
                # there should be a single place.
                s.append(node.replace('&', '&amp;').replace('<', '&lt;'))
            else:
                s.append(node.to_unicode(encoding=encoding))
        return u''.join(s)


    #######################################################################
    # Attributes
    def set_attribute(self, namespace, name, value, prefix=None):
        self.attributes[(namespace, name)] = value
        self.prefixes[namespace] = prefix


    def get_attribute(self, namespace, local_name):
        return self.attributes[(namespace, local_name)]


    def has_attribute(self, namespace, local_name):
        return (namespace, local_name) in self.attributes


    def get_attributes(self):
        for key, value in self.attributes.items():
            yield key[0], key[1], value


    def get_attribute_qname(self, namespace, local_name):
        """Returns the fully qualified name"""
        prefix = self.prefixes[namespace]
        if prefix is None:
            return local_name

        # Namespace declarations for the default namespace lack the local
        # name (e.g. xmlns="http://www.example.org"). Here 'xmlns' is always
        # the prefix, and there is not a local name. This an special case.
        if local_name is None:
            return prefix

        return '%s:%s' % (prefix, local_name)


    def get_attribute_type(self, namespace_uri, local_name):
        """
        Returns the type for the given attribute
        """
        namespace = namespaces.get_namespace(namespace_uri)
        schema = namespace.get_attribute_schema(local_name)
        return schema['type']


    #######################################################################
    # Children
    def set_comment(self, comment):
        self.children.append(comment)


    def set_element(self, element):
        self.children.append(element)


    def set_text(self, text, encoding='UTF-8'):
        text = types.Unicode.decode(text, encoding)
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


    def set_doctype_handler(cls, public_id, handler):
        cls.doctype_handlers[public_id] = handler

    set_doctype_handler = classmethod(set_doctype_handler)


    def get_doctype_handler(cls, public_id):
        return cls.doctype_handlers.get(public_id)

    get_doctype_handler = classmethod(get_doctype_handler)


    def has_doctype_handler(cls, public_id):
        return public_id in cls.doctype_handlers

    has_doctype_handler = classmethod(has_doctype_handler)


    #######################################################################
    # Load
    #######################################################################
    def _load_state(self, resource):
        """
        Builds a tree made of elements and raw data.
        """
        state = self.state
        # Default values
        state.xml_version = '1.0'
        state.source_encoding = 'UTF-8'
        state.standalone = -1
        state.document_type = None
        # Parse
        stack = []
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.XML_DECLARATION:
                state.xml_version = value[0]
                state.source_encoding = value[1]
                state.standalone = value[2]
            elif event == parser.DOCUMENT_TYPE:
                state.document_type = value
            elif event == parser.START_ELEMENT:
                namespace, prefix, local_name = value
                namespace = namespaces.get_namespace(namespace)
                try:
                    schema = namespace.get_element_schema(local_name)
                except XMLError, e:
                    e.line_number = line_number
                    raise e
                element_type = schema['type']
                element = element_type(prefix, local_name)
                stack.append(element)
            elif event == parser.END_ELEMENT:
                element = stack.pop()
                if stack:
                    stack[-1].set_element(element)
                else:
                    state.root_element = element
            elif event == parser.ATTRIBUTE:
                namespace_uri, prefix, local_name, value = value
                namespace = namespaces.get_namespace(namespace_uri)
                try:
                    schema = namespace.get_attribute_schema(local_name)
                except XMLError, e:
                    e.line_number = line_number
                    raise e
                attribute_type = schema['type']
                value = attribute_type.decode(value)
                stack[-1].set_attribute(namespace_uri, local_name, value,
                                        prefix=prefix)
            elif event == parser.COMMENT:
                stack[-1].set_comment(Comment(value))
            elif event == parser.TEXT:
                if stack:
                    stack[-1].set_text(value, 'UTF-8')

        # XXX This is an horrible hack
        from STL import STL
        self.stl = STL()
        self.stl.handler = self


    #######################################################################
    # API
    #######################################################################
    def header_to_unicode(self, encoding='UTF-8'):
        state = self.state

        s = []
        # The XML declaration
        if state.standalone == 1:
            pattern = u'<?xml version="%s" encoding="%s" standalone="yes"?>\n'
        elif state.standalone == 0:
            pattern = u'<?xml version="%s" encoding="%s" standalone="no"?>\n'
        else:
            pattern = u'<?xml version="%s" encoding="%s"?>\n'
        s.append(pattern % (state.xml_version, encoding))
        # The document type
        if state.document_type is not None:
            pattern = '<!DOCTYPE %s\n' \
                      '     PUBLIC "%s"\n' \
                      '    "%s">\n'
            s.append(pattern % state.document_type[:3])

        return u''.join(s)


    def to_unicode(self, encoding='UTF-8'):
        s = []
        s.append(self.header_to_unicode(encoding))
        # The children
        s.append(self.state.root_element.to_unicode(encoding))

        return u''.join(s)


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
    for event, value, line_number in parser.parse(resource.read()):
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
