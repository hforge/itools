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
from copy import copy
from HTMLParser import HTMLParser
from sets import Set

# Import from itools
from itools.handlers import File, IO
from itools.xml import XML, XHTML


#############################################################################
# Parser
#############################################################################
class Parser(HTMLParser, XML.Parser):

    def parse(self, data):
        # Defaults
        self.encoding = 'UTF-8'
        self.declaration = None

        # Initialize the data structure
        self.children = []

        # Parse
        self.stack = [self]
        self.feed(data)
        self.close()
        del self.stack

        return self


    def handle_decl(self, declaration):
        # XXX This is related with the XML doctype, we should share code
        self.declaration = declaration


    def handle_starttag(self, name, attrs):
        element_types = {'head': HeadElement}
        element_type = element_types.get(name, Element)
        element = element_type(None, name)

        for attr_name, value in attrs:
            element.set_attribute(None, attr_name, value)

        self.stack.append(element)

        # Check for the mime type and encoding
        if name == 'meta':
            if element.has_attribute(None, 'http-equiv'):
                http_equiv = element.get_attribute(None, 'http-equiv')
                if http_equiv == 'Content-Type':
                    value = element.get_attribute(None, 'content')
                    mimetype, charset = value.split(';')
                    self.mimetype = mimetype.strip()
                    self.encoding = charset.strip()[len('charset='):]

        # Close the tag if needed
        if name in empty_elements:
            XML.Parser.end_element_handler(self, name)


    def handle_endtag(self, name):
        # Ignore end tags without an start
        if name == getattr(self.stack[-1], 'name', None):
            XML.Parser.end_element_handler(self, name)


    def handle_comment(self, data):
        XML.Parser.comment_handler(self, data)


    handle_data = XML.Parser.char_data_handler


    def handle_entityref(self, name):
        XML.Parser.skipped_entity_handler(self, name, False)


    # XXX handlers that remain to implement include
##    def handle_pi(self, data):


    def close(self):
        while len(self.stack) > 1:
            XML.Parser.end_element_handler(self, self.stack[-1].name)
        HTMLParser.close(self)



#############################################################################
# Data types
#############################################################################

# List of empty elements, which don't have a close tag
empty_elements = Set(['area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
                      'img', 'input', 'isindex', 'link', 'meta', 'param'])

class Element(XHTML.Element):

    def get_closetag(self):
        if self.name in empty_elements:
            return ''
        return XHTML.Element.get_closetag(self)


class HeadElement(XHTML.Element):

    def to_unicode(self, encoding='UTF-8'):
        # XXX This is almost identical to 'XHTML.Element.to_unicode'
        return ''.join([self.get_opentag(),
                        '\n    <meta http-equiv="Content-Type" content="text/html; charset=%s">' % encoding,
                        XML.Children.encode(self.children, encoding=encoding),
                        self.get_closetag()])


#############################################################################
# Documents
#############################################################################

class Document(XHTML.Document):
    """
    HTML files are a lot like XHTML, only the parsing and the output is
    different, so we inherit from XHTML instead of Text, even if the
    mime type is 'text/html'.

    The parsing is based on the HTMLParser class, which has a more object
    oriented approach than the expat parser used for xml, i.e. we inherit
    from HTMLParser.
    """

    class_mimetypes = ['text/html']

    # HTML does not support XML namespace declarations
    ns_declarations = {}


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self, title=''):
        s = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n' \
            '  "http://www.w3.org/TR/html4/loose.dtd">\n' \
            '<html>\n' \
            '  <head>\n' \
            '    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n' \
            '    <title>%(title)s</title>\n' \
            '  </head>\n' \
            '  <body></body>\n' \
            '</html>'
        return s % {'title': title}


    #######################################################################
    # Load/Save
    #######################################################################
    def _load(self, resource):
        parser = Parser()
        state = parser.parse(resource.get_data())

        self._encoding = state.encoding
        self._declaration = state.declaration
        self.children = state.children


    def to_unicode(self, encoding='UTF-8'):
        s = u''
        # The declaration
        if self._declaration is not None:
            s = u'<!%s>' % self._declaration
        # The children
        for child in self.children:
            if isinstance(child, unicode):
                s +=  child
            else:
                s += child.to_unicode(encoding)
        return s


    def to_str(self, encoding='UTF-8'):
        s = u''
        # The declaration
        if self._declaration is not None:
            s = u'<!%s>' % self._declaration
        # The children
        for child in self.children:
            # XXX Fix <meta http-equiv="Content-Type" content="...">
            if isinstance(child, unicode):
                s += child
            else:
                s += child.to_unicode(encoding)

        return s.encode(encoding)


    #######################################################################
    # API
    #######################################################################
    def get_root_element(self):
        # XXX Probably this should work like XML
        for child in self.children:
            if isinstance(child, Element):
                return child


XHTML.Document.register_handler_class(Document)
