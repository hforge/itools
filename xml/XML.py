# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from copy import copy
import htmlentitydefs
import logging
from sets import Set
import sys
import warnings
from xml.parsers import expat

# Import from itools.handlers
from itools.handlers import File, Text


### Create a logger for dubugging
##import os
##try:
##    os.remove('/tmp/xml_debug.txt')
##except OSError:
##    pass
##logger = logging.getLogger('xml debug')
##logger.setLevel(logging.DEBUG)
##handler = logging.FileHandler('/tmp/xml_debug.txt')
##logger.addHandler(handler)



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



class Context(object):
    """
    The parameter 'context' expected by 'Document.walk' must be an instance
    of this class. For now it does two things:

    - keeps the path to the current node in the 'path' attibute

    - serves as a generic container for any specific data needed by the
      developers code

    XXX In the will provide the means to control the tree traversal, for
    example to prevent the traverse of a branch. This will allow to
    implement STL with walk.
    """

    def __init__(self):
        self.path = []



class Node(object):
    parent = None

    def traverse(self):
        yield self



class NodeList(list):
    def __unicode__(self):
        s = u''
        for node in self:
            s += unicode(node)
        return s


    def __str__(self):
        return unicode(self).encode('UTF-8')


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if len(self) != len(other):
            return 1
        for i in range(len(self)):
            if self[i] != other[i]:
                return 1
        return 0



class Raw(Node):
    def __init__(self, data):
        self.data = data


    def __unicode__(self):
        return self.data.replace('&', '&amp;').replace('<', '&lt;')


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(unicode(self), unicode(other))



class XMLDeclaration(Node):
    def __init__(self, version, encoding, standalone):
        self.version = version
        self.encoding = encoding
        self.standalone = standalone


    def __unicode__(self):
        if self.standalone == 1:
            return u'<?xml version="%s" encoding="%s" standalone="yes"?>' \
                   % (self.version, self.encoding)
        elif self.standalone == 0:
            return u'<?xml version="%s" encoding="%s" standalone="no"?>' \
                   % (self.version, self.encoding)
        else:
            return u'<?xml version="%s" encoding="%s"?>' \
                   % (self.version, self.encoding)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if self.version == other.version and self.encoding == other.encoding \
               and self.standalone == other.standalone:
            return 0
        return 1


    def copy(self):
        return XMLDeclaration(self.version, self.encoding, self.standalone)



class DocumentType(Node):
    def __init__(self, name, system_id, public_id, has_internal_subset):
        self.name = name
        self.system_id = system_id
        self.public_id = public_id
        self.has_internal_subset = has_internal_subset


    def __unicode__(self):
        # XXX The system and public ids maybe None
        pattern = '<!DOCTYPE %s' \
                  '\n     PUBLIC "%s"' \
                  '\n    "%s">'
        return pattern % (self.name, self.public_id, self.system_id)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if self.name == other.name and self.system_id == other.system_id \
               and self.public_id == other.public_id \
               and self.has_internal_subset == other.has_internal_subset:
            return 0
        return 1


class Comment(Node):
    def __init__(self, data):
        self.data = data


    def __unicode__(self):
        return u'<!--%s-->' % self.data


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.data, other.data)



class Attribute(object):
    namespace = None


    def __init__(self, prefix, name, value):
        self.prefix = prefix
        self.name = name
        self.value = value


    #######################################################################
    # API
    #######################################################################
    def get_qname(self):
        """Returns the fully qualified name"""
        if self.prefix is None:
            return self.name
        if self.name is None:
            return self.prefix
        return '%s:%s' % (self.prefix, self.name)

    qname = property(get_qname, None, None, '')


    def __unicode__(self):
        return '%s="%s"' % (self.qname, self.value)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if self.prefix == other.prefix and self.name == other.name \
               and self.value == other.value:
            return 0
        return 1


    def copy(self):
        return self.__class__(self.prefix, self.name, self.value)



class Attributes(dict):
    def __init__(self):
        # self[qname] = attribute
        dict.__init__(self)
        # self[uri][name] = attribute
        self.namespaces = {}


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if len(self) != len(other):
            return 1
        for key in self:
            if self[key] != other[key]:
                return 1
        return 0


    def __iter__(self):
        return iter(self.values())


    def add(self, attribute):
        qname = attribute.qname
        # self[qname] = attribue
        self[qname] = attribute
        # self[uri][name] = attribute
        uri = attribute.namespace
        namespace = self.namespaces.setdefault(uri, {})
        namespace[attribute.name] = attribute



class Element(Node):
    namespace = None


    def __init__(self, prefix, name):
        self.prefix = prefix
        self.name = name
        # Attributes (including namespace declarations)
        self.attributes = Attributes()
        # Child nodes
        self.children = NodeList()


    #######################################################################
    # DOM Level 3
    #######################################################################
    def append_child(self, child):
        # XXX Use weak references?
        child.parent = self
        self.children.append(child)


    def copy(self):
        """
        DOM: cloneNode.
        """
        # Build a new node
        clone = self.__class__(self.prefix, self.name)
        # Copy the attributes
        for attribute in self.attributes:
            attribute = attribute.copy()
            clone.attribues.add(attribute)
        # Copy the children
        for child in self.children:
            clone.append_child(child)
        return clone


    #######################################################################
    # Parsing
    #######################################################################
    def handle_attribute(self, ns_uri, prefix, name, value):
        # Get the namespace handler
        namespace = registry.get_namespace(ns_uri)
        # Create the attribute instance
        if namespace is None:
            attribute = Attribute(prefix, name, value)
        else:
            attribute = namespace.get_attribute(prefix, name, value)
        # Set the attribute
        self.attributes.add(attribute)


    def handle_start_element(self, ns_uri, prefix, name):
        # Get the namespace handler
        ns_handler = registry.get_namespace(ns_uri)

        # Create the element instance
        if ns_handler is None:
            element = Element(prefix, name)
        else:
            element = ns_handler.get_element(prefix, name)
        return element


    def handle_end_element(self, element):
        self.append_child(element)


    def handle_comment(self, data):
        comment = Comment(data)
        self.append_child(comment)


    def handle_rawdata(self, data):
        children = self.children
        if children and isinstance(children[-1], Raw):
            children[-1].data += data
        else:
            children.append(Raw(data))


    #######################################################################
    # API
    #######################################################################
    def get_qname(self):
        """Returns the fully qualified name"""
        if self.prefix is None:
            return self.name
        return '%s:%s' % (self.prefix, self.name)

    qname = property(get_qname, None, None, '')


    def __unicode__(self):
        return self.get_opentag() \
               + unicode(self.children) \
               + self.get_closetag()


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        if self.prefix == other.prefix and self.name == other.name \
               and self.attributes == other.attributes \
               and self.children == other.children:
            return 0
        return 1


    def get_opentag(self):
        s = '<%s' % self.qname
        # Output the attributes
        for attribute in self.attributes:
            s += ' ' + unicode(attribute)
        # Close the open tag
        return s + u'>'


    def get_closetag(self):
        return '</%s>' % self.qname


    def get_elements(self, name=None):
        elements = []
        for x in self.children:
            if isinstance(x, Element) and (name is None or x.name == name):
                elements.append(x)
        return elements


    def traverse(self):
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x


    def walk(self, before=None, after=None, context=None):
        """
        Traverse the tree, for each child do:

        1. call before
        2. traverse it
        3. call after
        """
        context.path.append(self)
        for child in self.children:
            if before is not None:
                stop = before(child, context)
            if not stop:
                if isinstance(child, Element):
                    child.walk(before, after, context)
            if after is not None:
                after(child, context)
        context.path.pop()


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

    class_id = 'text/xml'
    class_aliases = ['application/xml']
    class_ancestor = Text.Text


    #######################################################################
    # Load
    #######################################################################
    def _load(self, resource):
        """
        Builds a tree made of elements and raw data.
        """
        File.File._load(self, resource)
        # Default values for version, encoding and standalone are the expat's
        # default or implicit values. These are overwritten if a declaration
        # is found.
        self._version = '1.0'
        self._encoding = 'UTF-8' # XXX Should we call 'guess_encoding' instead?
        self._standalone = -1

        # Initialize the data structure
        self.children = NodeList()

        # Create the parser object
        parser = expat.ParserCreate(namespace_separator=' ')
        # Enable namespace declaration handlers
        parser.namespace_prefixes = True
        # Improve performance by reducing the calls to the default handler
        parser.buffer_text = True

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
        parser.Parse(self._data, True)

        # Remove auxiliar attributes
        del self.parser
        del self.stack
        del self.ns_declarations
        # Remove the processed data
        del self._data


    #######################################################################
    # expat handlers
    def xml_declaration_handler(self, version, encoding, standalone):
        xml_declaration = XMLDeclaration(version, encoding, standalone)
        self.children.append(xml_declaration)


    def start_doctype_handler(self, name, system_id, public_id,
                              has_internal_subset):
        doctype = DocumentType(name, system_id, public_id, has_internal_subset)
        self.children.append(doctype)


    def end_doctype_handler(self):
        pass


    def start_namespace_handler(self, prefix, uri):
        if registry.has_namespace(uri):
            ns_handler = registry.get_namespace(uri)
            if hasattr(ns_handler, 'namespace_handler'):
                ns_handler.namespace_handler(self)
        else:
            warnings.warn('Unknown xml namespace: %s' % uri)        
        # Keep the namespace declarations
        self.ns_declarations[prefix] = uri


    def end_namespace_handler(self, prefix):
        pass


    def comment_handler(self, data):
        element = self.stack[-1]
        element.handle_comment(data)


    def start_element_handler(self, name, attrs):
##        logger.debug('XML.Document.start_element_handler(%s)', name)
        # Parse the element name: ns_uri, name and prefix
        n = name.count(' ')
        if n == 2:
            ns_uri, name, prefix = name.split()
        elif n == 1:
            prefix = None
            ns_uri, name = name.split()
        else:
            prefix = None
            ns_uri = None

        element = self.stack[-1]
        try:
            element = element.handle_start_element(ns_uri, prefix, name)
        except XMLError, e: 
            # Add the line number information
            e.line_number = self.parser.ErrorLineNumber
            raise e

        element_uri = ns_uri

        # Keep the namespace declarations (set them as attributes)
        for prefix, uri in self.ns_declarations.items():
            element.handle_attribute('http://www.w3.org/2000/xmlns/', 'xmlns',
                                     prefix, uri)
        self.ns_declarations = {}
        # Set the attributes
        for name, value in attrs.items():
            # Parse the attribute name: ns_uri, name and prefix
            if ' ' in name:
                ns_uri, name, prefix = name.split()
            else:
                prefix = None
                ns_uri = element_uri

            try:
                element.handle_attribute(ns_uri, prefix, name, value)
            except XMLError, e:
                # Add the line number information
                e.line_number = self.parser.ErrorLineNumber
                raise e

        self.stack.append(element)
        return element


    def end_element_handler(self, name):
        element = self.stack.pop()
        parent = self.stack[-1]
        parent.handle_end_element(element)


    def char_data_handler(self, data):
        element = self.stack[-1]
        element.handle_rawdata(data)


    def skipped_entity_handler(self, name, is_param_entity):
        # XXX HTML specific
        codepoint = htmlentitydefs.name2codepoint[name]
        char = unichr(codepoint)
        self.char_data_handler(char)


    def default_handler(self, data):
        self.char_data_handler(data)


    #######################################################################
    # itools.xml handlers
    def handle_start_element(self, ns_uri, prefix, name):
        # Get the namespace handler
        ns_handler = registry.get_namespace(ns_uri)

        # Create the element instance
        if ns_handler is None:
            element = Element(prefix, name)
        else:
            element = ns_handler.get_element(prefix, name)
        return element


    def handle_end_element(self, element):
        self.children.append(element)


    def handle_rawdata(self, data):
        children = self.children
        if children and isinstance(children[-1], Raw):
            children[-1].data += data
        else:
            children.append(Raw(data))


    #######################################################################
    # API
    #######################################################################
    def to_unicode(self):
        # The children
        s = u''
        for child in self.children:
            s += unicode(child)
        return s


    def to_str(self, encoding='UTF-8'):
        # The children
        s = u''
        for child in self.children:
            if isinstance(child, XMLDeclaration):
                child = copy(child)
                child.encoding = encoding
            s += unicode(child)

        return s.encode(encoding)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.children, other.children)


    def get_root_element(self):
        """
        Returns the root element (XML documents have one root element).
        """
        for child in self.children:
            if isinstance(child, Element):
                return child
        return None
##        raise XMLError, 'XML document has not a root element!!'


    def traverse(self):
        yield self
        for child in self.children:
            for x in child.traverse():
                yield x


    def walk(self, before=None, after=None, context=None):
        """
        Traverse the tree, for each child do:

        1. before(child, context)
        2. traverse it
        3. after(child, context)
        """
        if context is None:
            context = Context()

        context.path.append(self)
        for child in self.children:
            if before is not None:
                before(child, context)
            if isinstance(child, Element):
                child.walk(before, after, context)
            if after is not None:
                after(child, context)
        context.path.pop()



#############################################################################
# The Registry
#############################################################################
class Registry(object):
    """
    Keeps account of namespace and document types handlers.
    """

    def __init__(self):
        self.namespaces = {}
        self.doctypes = {}


    def set_namespace(self, uri, handler):
        self.namespaces[uri] = handler


    def get_namespace(self, uri):
        return self.namespaces.get(uri)


    def has_namespace(self, uri):
        return uri in self.namespaces


    def set_doctype(self, public_id, handler):
        self.doctypes[public_id] = handler


    def get_doctype(self, public_id):
        return self.doctypes.get(public_id)


    def has_doctype(self, public_id):
        return public_id in self.doctypes


registry = Registry()



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

