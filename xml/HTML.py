# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.handlers import File
import XHTML



# List of empty elements, which don't have a close tag
empty_elements = Set(['area', 'base', 'basefont', 'br', 'col', 'frame', 'hr',
                      'img', 'input', 'isindex', 'link', 'meta', 'param'])

class Element(XHTML.Element):
    def get_closetag(self):
        if self.name in empty_elements:
            return ''
        return XHTML.Element.get_closetag(self)



class Document(XHTML.Document, HTMLParser):
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
    # Parsing
    #######################################################################
    def _load(self, resource):
        File.File._load(self, resource)
        # Initialize the parser
        HTMLParser.__init__(self)

        # Defaults
        self._encoding = 'UTF-8'
        self._declaration = None

        # Initialize the data structure
        self.children = []

        # Parse
        self.stack = [self]
        self.feed(self._data)
        self.close()
        del self.stack

        # Remove the original data, don't neet it anymore
        del self._data


    def handle_decl(self, decl):
        # XXX This is related with the XML doctype, we should share code
        self._declaration = decl


    def handle_starttag(self, name, attrs):
        element = Element(None, name)

        for attr_name, value in attrs:
            element.set_attribute(attr_name, value)

        self.stack.append(element)

        # Check for the mime type and encoding
        if name == 'meta':
            if element.has_attribute('http-equiv'):
                http_equiv = element.get_attribute('http-equiv')
                if http_equiv == 'Content-Type':
                    value = element.get_attribute('content')
                    mimetype, charset = value.split(';')
                    self._mimetype = mimetype.strip()
                    self._encoding = charset.strip()[len('charset='):]

        # Close the tag if needed
        if name in empty_elements:
            XHTML.Document.end_element_handler(self, name)


    def handle_endtag(self, name):
        # Ignore end tags without an start
        if name == getattr(self.stack[-1], 'name', None):
            XHTML.Document.end_element_handler(self, name)


    def handle_comment(self, data):
        XHTML.Document.comment_handler(self, data)


    handle_data = XHTML.Document.default_handler


    def handle_entityref(self, name):
        XHTML.Document.skipped_entity_handler(self, name, False)


    # XXX handlers that remain to implement include
##    def handle_comment(self, data):
##    def handle_pi(self, data):


    def close(self):
        while len(self.stack) > 1:
            XHTML.Document.end_element_handler(self, self.stack[-1].name)
        HTMLParser.close(self)


    #######################################################################
    # API
    #######################################################################
    def to_unicode(self):
        s = u''
        # The declaration
        if self._declaration is not None:
            s = u'<!%s>' % self._declaration
        # The children
        for child in self.children:
            s += unicode(child)
        return s


    def to_str(self, encoding='UTF-8'):
        s = u''
        # The declaration
        if self._declaration is not None:
            s = u'<!%s>' % self._declaration
        # The children
        for child in self.children:
            # XXX Fix <meta http-equiv="Content-Type" content="...">
            s += unicode(child)

        return s.encode(encoding)


XHTML.Document.register_handler_class(Document)
