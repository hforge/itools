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
import htmlentitydefs
import warnings
from xml.parsers import expat

# Import from itools
from itools.xml import namespaces


XML_DECLARATION, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, ATTRIBUTE, \
                 COMMENT, TEXT = range(7)



class Parser(object):

    encoding = 'UTF-8'


    def parse(self, data):
        self.namespaces = {}

        # Create the parser object
        parser = expat.ParserCreate(namespace_separator=' ')

        # Enable namespace declaration handlers
        parser.namespace_prefixes = True
        # Improve performance by reducing the calls to the default handler
        parser.buffer_text = True
        # Do the "de-serialization" ourselves.
        # Note that expat always will return strings encoded in UTF-8,
        # regardless of the sourc encoding. This is sub-optimal from a
        # performance point of view, yet another reason to get rid of
        # expat.
        parser.returns_unicode = False

        # Set parsing handlers (XXX there are several not yet supported)
        parser.XmlDeclHandler = self.xml_declaration_handler
        parser.StartDoctypeDeclHandler = self.start_doctype_handler
##        parser.EndDoctypeDeclHandler = self.end_doctype_handler
##        parser.ElementDeclHandler =
##        parser.AttlistDeclHandler =
##        parser.ProcessingInstructionHandler =
        parser.CharacterDataHandler = self.char_data_handler
        parser.StartElementHandler = self.start_element_handler
        parser.EndElementHandler = self.end_element_handler
##        parser.UnparsedEntityDeclHandler =
##        parser.EntityDeclHandler =
##        parser.NotatioDeclHandler =
        parser.StartNamespaceDeclHandler = self.start_namespace_handler
##        parser.EndNamespaceDeclHandler = self.end_namespace_handler
        parser.CommentHandler = self.comment_handler
##        parser.StartCdataSectionHandler =
##        parser.EndCdataSectionHandler =
        parser.DefaultHandler = self.default_handler
##        parser.DefaultHandlerExpand =
##        parser.NotStandaloneHandler =
##        parser.ExternalEntityRefHandler =
        parser.SkippedEntityHandler = self.skipped_entity_handler

        # Needed to get the line number
        self.parser = parser

        # Initialize values
        self.events = []
        parser.Parse(data, True)
        return self.events


    def xml_declaration_handler(self, version, encoding, standalone):
        if encoding is None:
            encoding = 'UTF-8'
        self.encoding = encoding
        self.events.append((XML_DECLARATION, (version, encoding, standalone),
                            self.parser.ErrorLineNumber))


    def start_doctype_handler(self, name, system_id, public_id,
                              has_internal_subset):
        has_internal_subset = bool(has_internal_subset)
        self.events.append((DOCUMENT_TYPE,
                            (name, system_id, public_id, has_internal_subset),
                            self.parser.ErrorLineNumber))


    def start_element_handler(self, name, attrs):
        # Parse the element name: namespace_uri, name and prefix
        n = name.count(' ')
        if n == 2:
            namespace, name, prefix = name.split()
        elif n == 1:
            prefix = None
            namespace, name = name.split()
        else:
            prefix = None
            namespace = None

        # Start Element
        self.events.append((START_ELEMENT, (namespace, prefix, name),
                            self.parser.ErrorLineNumber))
        element_uri = namespace

        # Keep the namespace declarations
        for name, value in self.namespaces.items():
            xmlns_namespace = namespaces.XMLNSNamespace
            self.events.append((ATTRIBUTE, (xmlns_namespace.class_uri,
                                            xmlns_namespace.class_prefix,
                                            name, value),
                                self.parser.ErrorLineNumber))
        self.namespaces = {}

        # Attributes
        for name, value in attrs.items():
            # Parse the attribute name: namespace_uri, name and prefix
            n = name.count(' ')
            if n == 2:
                namespace, name, prefix = name.split()
            elif n == 1:
                namespace, name = name.split()
                if namespace == namespaces.xml:
                    prefix = 'xml'
                else:
                    prefix = None
            else:
                prefix = None
                namespace = element_uri

            self.events.append((ATTRIBUTE, (namespace, prefix, name, value),
                                self.parser.ErrorLineNumber))


    def end_element_handler(self, name):
        # Parse the element name: namespace_uri, name and prefix
        n = name.count(' ')
        if n == 2:
            namespace, name, prefix = name.split()
        elif n == 1:
            prefix = None
            namespace, name = name.split()
        else:
            prefix = None
            namespace = None

        self.events.append((END_ELEMENT, (namespace, prefix, name),
                            self.parser.ErrorLineNumber))


    def start_namespace_handler(self, prefix, uri):
        self.namespaces[prefix] = uri


    def char_data_handler(self, data):
        self.events.append((TEXT, data, self.parser.ErrorLineNumber))


    def comment_handler(self, data):
        self.events.append((COMMENT, data, self.parser.ErrorLineNumber))


    def default_handler(self, data):
        self.events.append((TEXT, data, self.parser.ErrorLineNumber))


    def skipped_entity_handler(self, name, is_param_entity):
        # XXX HTML specific
        if name in htmlentitydefs.name2codepoint:
            codepoint = htmlentitydefs.name2codepoint[name]
            char = unichr(codepoint).encode('UTF-8')
            self.events.append((TEXT, char, self.parser.ErrorLineNumber))
        else:
            warnings.warn('Unknown entity reference "%s" (ignoring)' % name)



def parse(data):
    parser = Parser()
    return parser.parse(data)
