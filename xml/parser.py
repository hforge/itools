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
from xml.parsers import expat

# Import from itools
from itools.xml import namespaces


XML_DECLARATION, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, ATTRIBUTE, \
                 COMMENT, TEXT = range(7)



class Parser(object):

    def parse(self, data):
        self.namespaces = {}

        # Create the parser object
        parser = expat.ParserCreate(namespace_separator=' ')

        # Improve performance by reducing the calls to the default handler
        parser.buffer_text = True
        # Do the "de-serialization" ourselves.
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

        # Initialize values
        self.events = []
        for x in data:
            parser.Parse(x)
            for event, value in self.events:
                yield event, value, parser.ErrorLineNumber
                # Reset values
                self.events = []
        # End parsing
        parser.Parse('', True)


    def xml_declaration_handler(self, version, encoding, standalone):
        if encoding is None:
            encoding = 'UTF-8'
        self.events.append((XML_DECLARATION, (version, encoding, standalone)))


    def start_doctype_handler(self, name, system_id, public_id,
                              has_internal_subset):
        has_internal_subset = bool(has_internal_subset)
        self.events.append((DOCUMENT_TYPE,
                            (name, system_id, public_id, has_internal_subset)))


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
        self.events.append((START_ELEMENT, (namespace, prefix, name)))
        element_uri = namespace

        # Keep the namespace declarations
        for name, value in self.namespaces.items():
            self.events.append((ATTRIBUTE,
                                (namespaces.xml, 'xmlns', name, value)))
        self.namespaces = {}

        # Attributes
        for name, value in attrs.items():
            # Parse the attribute name: namespace_uri, name and prefix
            if ' ' in name:
                namespace, name, prefix = name.split()
            else:
                prefix = None
                namespace = element_uri

            self.events.append((ATTRIBUTE, (namespace, prefix, name, value)))


    def end_element_handler(self, name):
        self.events.append((END_ELEMENT, None))


    def start_namespace_handler(self, prefix, uri):
        self.namespaces[prefix] = uri


    def char_data_handler(self, data):
        self.events.append((TEXT, data))


    def comment_handler(self, data):
        self.events.append((COMMENT, data))


    def default_handler(self, data):
        self.events.append((TEXT, data))


    def skipped_entity_handler(self, name, is_param_entity):
        # XXX HTML specific
        if name in htmlentitydefs.name2codepoint:
            codepoint = htmlentitydefs.name2codepoint[name]
            char = unichr(codepoint).encode(self.encoding)
            self.events.append((TEXT, char))
        else:
            warnings.warn('Unknown entity reference "%s" (ignoring)' % name)



parser = Parser()
