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
from HTMLParser import HTMLParser
from sets import Set
import warnings



DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, ATTRIBUTE, COMMENT, TEXT = range(6)


# List of empty elements, which don't have a close tag
empty_elements = Set(['area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
                      'img', 'input', 'isindex', 'link', 'meta', 'param'])



class Parser(HTMLParser):

    def parse(self, data):
        
        self.encoding = 'UTF-8'

        self.events = []
        for x in data:
            self.feed(x)
            for event, value in self.events:
                line_number, offset = self.getpos()
                yield event, value, line_number
                # Reset values
                self.events = []

        self.close()


    def handle_decl(self, declaration):
        # XXX This is related with the XML doctype, it should have a similar
        # structure.
        self.events.append((DOCUMENT_TYPE, declaration))


    def handle_starttag(self, name, attrs):
        # Start element
        self.events.append((START_ELEMENT, name))

        # Attributes
        for attribute in attrs:
            self.events.append((ATTRIBUTE, attribute))

        # End element
        if name in empty_elements:
            self.events.append((END_ELEMENT, name))


    def handle_endtag(self, name):
        self.events.append((END_ELEMENT, name))


    def handle_comment(self, data):
        self.events.append((COMMENT, data))


    def handle_data(self, data):
        self.events.append((TEXT, data))


    def handle_entityref(self, name):
        # XXX Copied from 'itools.xml.parser.Parser.skipped_entity_handler'
        if name in htmlentitydefs.name2codepoint:
            codepoint = htmlentitydefs.name2codepoint[name]
            char = unichr(codepoint).encode(self.encoding)
            self.events.append((TEXT, char))
        else:
            warnings.warn('Unknown entity reference "%s" (ignoring)' % name)


    # XXX handlers that remain to implement include
##    def handle_pi(self, data):
