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


# Import from Python
from copy import copy, deepcopy
import htmlentitydefs
import logging
from sets import Set
import sys
import warnings
from xml.parsers import expat

# Import from itools
from itools.handlers import File, Text, IO



#############################################################################
# Exceptions
#############################################################################

class XMLError(Exception):
    """
    The expat parser checks the document to be well formed, if it is not
    the ExpatError exception is raised.

    The XMLError exception (or a subclass of it) should be raised when
    the document does not conform to an schema. For an example see how
    it is used by the STL language.

    Note that right now we don't automatically check against DTD's or
    schemas (that's something to do: XXX), so your namespace handler must
    verify the correctness itself.
    """

    def __init__(self, message):
        self.message = message
        self.line_number = None


    def __str__(self):
        if self.line_number is not None:
            return '%s, line %s' % (self.message, self.line_number)
        return self.message


#############################################################################
# Parser
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



class Parser(object):

    def parse(self, data):
        # Default values for version, encoding and standalone are the expat's
        # default or implicit values. These are overwritten if a declaration
        # is found.
        self.version = '1.0'
        self.encoding = 'UTF-8' # XXX Should we call 'guess_encoding' instead?
        self.standalone = -1

        self.document_type = None

        # Initialize the data structure
        self.children = []

        # Create the parser object
        parser = expat.ParserCreate(namespace_separator=' ')
        # Enable namespace declaration handlers
        parser.namespace_prefixes = True
        # Improve performance by reducing the calls to the default handler
        parser.buffer_text = True
        # Do the "de-serialization" ourselves.
        parser.returns_unicode = False

        # Set parsing handlers (XXX there are several not yet supported)
        parser.XmlDeclHandler = self.xml_declaration_handler
        parser.StartDoctypeDeclHandler = self.start_doctype_handler
        parser.EndDoctypeDeclHandler = self.end_doctype_handler
##        parser.ElementDeclHandler =
##        parser.AttlistDeclHandler =
        parser.StartElementHandler = self.start_element_handler
        parser.EndElementHandler = self.end_element_handler
##        parser.ProcessingInstructionHandler =
        parser.CharacterDataHandler = self.char_data_handler
##        parser.UnparsedEntityDeclHandler =
##        parser.EntityDeclHandler =
##        parser.NotatioDeclHandler =
        parser.StartNamespaceDeclHandler = self.start_namespace_handler
        parser.EndNamespaceDeclHandler = self.end_namespace_handler
        parser.CommentHandler = self.comment_handler
##        parser.StartCdataSectionHandler =
##        parser.EndCdataSectionHandler = 
        parser.DefaultHandler = self.default_handler
##        parser.DefaultHandlerExpand =
##        parser.NotStandaloneHandler =
##        parser.ExternalEntityRefHandler =
        parser.SkippedEntityHandler = self.skipped_entity_handler

        # The parser, so we keep the error information
        self.parser = parser
        # Stack with the still open elements
        self.stack = [self]
        # The last namespace declaration
        self.ns_declarations = {}

        # Parse!!
        parser.Parse(data, True)

        # Remove auxiliar attributes
        del self.parser
        del self.stack
        del self.ns_declarations

        return self


    #######################################################################
    # expat handlers
    #######################################################################
    def xml_declaration_handler(self, version, encoding, standalone):
        self.version = version
        if encoding is not None:
            self.encoding = encoding
        self.standalone = standalone


    def start_doctype_handler(self, name, system_id, public_id,
                              has_internal_subset):
        self.document_type = (name, system_id, public_id, has_internal_subset)


    def end_doctype_handler(self):
        pass


    def start_namespace_handler(self, prefix, uri):
        namespace_handler = get_namespace(uri)
        namespace_handler.namespace_handler(self)
        # Keep the namespace declarations
        self.ns_declarations[prefix] = uri


    def end_namespace_handler(self, prefix):
        pass


    def comment_handler(self, data):
        element = self.stack[-1]

        comment = Comment(data)
        element.set_comment(comment)


    def start_element_handler(self, name, attrs):
        # Parse the element name: namespace_uri, name and prefix
        n = name.count(' ')
        if n == 2:
            namespace_uri, name, prefix = name.split()
        elif n == 1:
            prefix = None
            namespace_uri, name = name.split()
        else:
            prefix = None
            namespace_uri = None

        # Load the namespace handler
        namespace = get_namespace(namespace_uri)
        # Load the element
        try:
            element = namespace.get_element(prefix, name)
        except XMLError, e:
            # Add the line number information
            e.line_number = self.parser.ErrorLineNumber
            raise e

        element_uri = namespace_uri

        # Keep the namespace declarations (set them as attributes)
        xmlns_uri = 'http://www.w3.org/2000/xmlns/'
##        xmlns = get_namespace(xmlns_uri)
        xmlns = get_namespace(None)
        for name, value in self.ns_declarations.items():
            value = xmlns.get_attribute('xmlns', name, value)
            element.set_attribute(name, value, namespace=xmlns_uri,
                                  prefix='xmlns')
        self.ns_declarations = {}
        # Set the attributes
        for name, value in attrs.items():
            # Parse the attribute name: namespace_uri, name and prefix
            if ' ' in name:
                namespace_uri, name, prefix = name.split()
            else:
                prefix = None
                namespace_uri = element_uri

            namespace = get_namespace(namespace_uri)
            try:
                attribute = namespace.get_attribute(prefix, name,value)
            except XMLError, e:
                # Add the line number information
                e.line_number = self.parser.ErrorLineNumber
                raise e
            else:
                element.set_attribute(name, attribute, namespace=namespace_uri,
                                      prefix=prefix)

        self.stack.append(element)
        return element


    def end_element_handler(self, name):
        element = self.stack.pop()
        parent = self.stack[-1]
        parent.set_element(element)


    def char_data_handler(self, data):
        element = self.stack[-1]
        element.set_text(data, self.encoding)


    def skipped_entity_handler(self, name, is_param_entity):
        # XXX HTML specific
        if name in htmlentitydefs.name2codepoint:
            codepoint = htmlentitydefs.name2codepoint[name]
            char = unichr(codepoint).encode(self.encoding)
            self.char_data_handler(char)
        else:
            warnings.warn('Unknown entity reference "%s" (ignoring)' % name)


    def default_handler(self, data):
        self.char_data_handler(data)


    #######################################################################
    # Private API
    #######################################################################
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



#############################################################################
# Namespaces
#############################################################################

namespaces = {}


def set_namespace(uri, handler):
    namespaces[uri] = handler


def get_namespace(uri):
    if uri in namespaces:
        return namespaces[uri]
    # Use default 
    warnings.warn('Unknown namespace "%s" (using default)' % uri)
    return namespaces[None]


def has_namespace(uri):
    return uri in namespaces



class Namespace(object):
    """
    Default namespace handler for elements and attributes that are not bound
    to a particular namespace.
    """

    def namespace_handler(cls, document):
        pass

    namespace_handler = classmethod(namespace_handler)


    def get_element(cls, prefix, name):
        return Element(prefix, name)

    get_element = classmethod(get_element)


    def get_attribute(cls, prefix, name, value):
        return IO.Unicode.decode(value)

    get_attribute = classmethod(get_attribute)


# Set the default namespace
set_namespace(None, Namespace)
    


#############################################################################
# Data types
#############################################################################

class Comment(object):

    parent = None

    def __init__(self, data):
        self.data = data


    def to_unicode(self, encoding='UTF-8'):
        return u'<!--%s-->' % self.data


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.data, other.data)



class Element(object):

    parent = None
    namespace = None


    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name
        # Attributes (including namespace declarations)
        self.attributes = {}
        self.attributes_by_qname = {}
        # Child nodes
        self.children = []


    #######################################################################
    # API
    #######################################################################
    def get_qname(self):
        """Returns the fully qualified name"""
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
        clone.attributes = deepcopy(self.attributes)
        clone.attributes_by_qname = deepcopy(self.attributes_by_qname)
        # Copy the children (XXX)
        clone.children = deepcopy(self.children)
##        for child in self.children:
##            clone.append_child(child)
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
        return self.get_opentag(encoding) \
               + Children.encode(self.children, encoding=encoding) \
               + self.get_closetag()


    def get_opentag(self, encoding='UTF-8'):
        s = '<%s' % self.qname
        # Output the attributes
        for qname, value in self.attributes_by_qname.items():
            s += ' %s="%s"' % (qname, unicode(value))
        # Close the open tag
        return s + u'>'


    def get_closetag(self):
        return '</%s>' % self.qname


    #######################################################################
    # Attributes
    def set_attribute(self, name, value, namespace=None, prefix=None):
        self.attributes[(namespace, name)] = value
        if prefix is None:
            qname = name
        elif name is None:
            qname = prefix
        else:
            qname = '%s:%s' % (prefix, name)
        self.attributes_by_qname[qname] = value


    def get_attribute(self, name, namespace=None):
        if namespace is None:
            return self.attributes_by_qname[name]
        return self.attributes[(namespace, name)]


    def has_attribute(self, name, namespace=None):
        if namespace is None:
            return name in self.attributes_by_qname
        return (namespace, name) in self.attributes


    def get_attributes(self):
        for key in self.attributes:
            yield key[0], key[1], self.attributes[key]


    #######################################################################
    # Children
    def set_comment(self, comment):
        self.children.append(comment)


    def set_element(self, element):
        # XXX Use weak references?
        element.parent = self
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
        # Parse
        parser = Parser()
        state = parser.parse(resource.get_data())
        # Declaration
        self._version = state.version
        self._encoding = state.encoding
        self._standalone = state.standalone
        # Document type
        self.document_type = state.document_type
        # Children
        elements = [ x for x in state.children if isinstance(x, Element) ]
        self.root_element = elements[0]

        # XXX This is horrible
        if hasattr(state, 'stl'):
            self.stl = state.stl


    #######################################################################
    # API
    #######################################################################
    def to_unicode(self, encoding='UTF-8'):
        s = []
        # The XML declaration
        if self._standalone == 1:
            pattern = u'<?xml version="%s" encoding="%s" standalone="yes"?>\n'
        elif self._standalone == 0:
            pattern = u'<?xml version="%s" encoding="%s" standalone="no"?>\n'
        else:
            pattern = u'<?xml version="%s" encoding="%s"?>\n'
        s.append(pattern % (self._version, encoding))
        # The document type
        if self.document_type is not None:
            pattern = '<!DOCTYPE %s' \
                      '\n     PUBLIC "%s"' \
                      '\n    "%s">'
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
        for x in self.root_element.traverse():
            yield x


    def traverse2(self, context=None):
        if context is None:
            context = Context()
        # Children
        for x, context in self.root_element.traverse2(context):
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



