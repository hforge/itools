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
from xml.parsers import expat

# Import from itools
from itools.handlers import File, Text, IO
from itools.xml.exceptions import XMLError
from itools.xml import namespaces
from itools.xml import parser


#############################################################################
# Data types
#############################################################################

class Children(object):

    def encode(cls, value, encoding='UTF-8'):
        s = []
        for node in value:
            if isinstance(node, unicode):
                s.append(node)
            else:
                s.append(node.to_unicode(encoding=encoding))
        return ''.join(s)

    encode = classmethod(encode)


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
        return self.get_opentag() \
               + Children.encode(self.children, encoding=encoding) \
               + self.get_closetag()


    def get_opentag(self):
        s = '<%s' % self.qname
        # Output the attributes
        for namespace_uri, local_name, value in self.get_attributes():
            qname = self.get_attribute_qname(namespace_uri, local_name)
            type = self.get_attribute_type(namespace_uri, local_name)
            value = type.to_unicode(value)
            s += ' %s="%s"' % (qname, value)
        # Close the open tag
        return s + u'>'


    def get_closetag(self):
        return '</%s>' % self.qname


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
        text = IO.Unicode.decode(text, encoding)
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


    # Default values
    xml_version = '1.0'
    source_encoding = 'UTF-8'
    standalone = -1
    document_type = None
    

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
    def _load(self, resource):
        """
        Builds a tree made of elements and raw data.
        """
        stack = []
        for event, value, line_number in parser.parse(resource.read()):
            if event == parser.XML_DECLARATION:
                self.xml_version, self.source_encoding, self.standalone = value
            elif event == parser.DOCUMENT_TYPE:
                self.document_type = value
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
                    self.root_element = element
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
    def to_unicode(self, encoding='UTF-8'):
        s = []
        # The XML declaration
        if self.standalone == 1:
            pattern = u'<?xml version="%s" encoding="%s" standalone="yes"?>\n'
        elif self.standalone == 0:
            pattern = u'<?xml version="%s" encoding="%s" standalone="no"?>\n'
        else:
            pattern = u'<?xml version="%s" encoding="%s"?>\n'
        s.append(pattern % (self.xml_version, encoding))
        # The document type
        if self.document_type is not None:
            pattern = '<!DOCTYPE %s\n' \
                      '     PUBLIC "%s\n"' \
                      '    "%s">\n'
            s.append(pattern % self.document_type[:3])
        # The children
        s.append(self.root_element.to_unicode(encoding))

        return ''.join(s)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        # XXX Remains to compare the declaration and the document type
        return cmp(self.root_element, other.root_element)


    def get_root_element(self):
        """
        Returns the root element (XML documents have one root element).
        """
        return self.root_element


    def traverse(self):
        for x in self.get_root_element().traverse():
            yield x


    def traverse2(self, context=None):
        if context is None:
            context = Context()
        # Children
        for x, context in self.get_root_element().traverse2(context):
            yield x, context


#############################################################################
# XML Factory
#############################################################################
class StopOracle(Exception):
    pass


class Oracle(object):
    def guess_doctype(self, resource):
        data = resource.get_data()
        self._doctype = None

        parser = expat.ParserCreate()
        parser.StartDoctypeDeclHandler = self.start_doctype_handler
        parser.StartElementHandler = self.start_element_handler
        try:
            parser.Parse(data, True)
        except StopOracle:
            doctype = self._doctype
            del self._doctype
            return doctype


    def start_doctype_handler(self, name, system_id, public_id,
                              has_internal_subset):
        self._doctype = public_id
        raise StopOracle


    def start_element_handler(self, nale, attrs):
        raise StopOracle



def get_handler(resource):
    """
    Factory for XML handlers. From a given resource, try to guess its document
    type, and return the proper XML handler.
    """
    oracle = Oracle()

    doctype = oracle.guess_doctype(resource)
    if registry.has_doctype(doctype):
        handler_class = registry.get_doctype(doctype)
    else:
        handler_class = Document
    return handler_class(resource)


Text.Text.register_handler_class(Document)



