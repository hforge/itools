# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.datatypes import Unicode
from itools.schemas import get_datatype_by_uri
from itools.handlers import File, register_handler_class
from itools.xml import Comment
from itools.xhtml import Document as XHTMLDocument, Element
from parser import (Parser, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT,
                    COMMENT, TEXT)


ns_uri = 'http://www.w3.org/1999/xhtml'



elements_schema = {
    'a': {'type': Element, 'is_inline': True},
    'abbr': {'type': Element, 'is_inline': True},
    'acronym': {'type': Element, 'is_inline': True},
    'b': {'type': Element, 'is_inline': True},
    'cite': {'type': Element, 'is_inline': True},
    'code': {'type': Element, 'is_inline': True},
    'dfn': {'type': Element, 'is_inline': True},
    'em': {'type': Element, 'is_inline': True},
    'head': {'type': Element, 'is_inline': False},
    'kbd': {'type': Element, 'is_inline': True},
    'q': {'type': Element, 'is_inline': True},
    'samp': {'type': Element, 'is_inline': True},
    'span': {'type': Element, 'is_inline': True},
    'strong': {'type': Element, 'is_inline': True},
    'sub': {'type': Element, 'is_inline': True},
    'sup': {'type': Element, 'is_inline': True},
    'tt': {'type': Element, 'is_inline': True},
    'var': {'type': Element, 'is_inline': True},
    }


#############################################################################
# Documents
#############################################################################

class Document(XHTMLDocument):
    """
    HTML files are a lot like XHTML, only the parsing and the output is
    different, so we inherit from XHTML instead of Text, even if the
    mime type is 'text/html'.

    The parsing is based on the HTMLParser class, which has a more object
    oriented approach than the expat parser used for xml, i.e. we inherit
    from HTMLParser.
    """

    class_mimetypes = ['text/html']
    class_extension = 'html'

    # HTML does not support XML namespace declarations
    ns_declarations = {}

    
    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'document_type', 'root_element', 'encoding']


    #########################################################################
    # The skeleton
    #########################################################################
    @classmethod
    def get_skeleton(cls, title=''):
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


    def to_str(self, encoding='UTF-8'):
        root = self.get_root_element()
        data = [self.header_to_str(encoding),
                element_to_str_as_html(root, encoding)]

        return ''.join(data)


    #######################################################################
    # Load/Save
    #######################################################################
    def _load_state_from_file(self, file):
        self.encoding = 'UTF-8'
        self.document_type = None
        children = []

        stack = []
        data = file.read()
        parser = Parser()
        for event, value, line_number in parser.parse(data):
            if event == DOCUMENT_TYPE:
                self.document_type = value
            elif event == START_ELEMENT:
                name, attributes = value
                schema = elements_schema.get(name, {'type': Element,
                                                    'is_inline': False})
                element_class = schema['type']
                element = element_class(ns_uri, name)
                for attr_name in attributes:
                    attr_value = attributes[attr_name]
                    type = get_datatype_by_uri(ns_uri, attr_name)
                    attr_value = type.decode(attr_value)
                    element.set_attribute(element.namespace, attr_name, attr_value)
                stack.append(element)
            elif event == END_ELEMENT:
                element = stack.pop()

                # Detect <meta http-equiv="Content-Type" content="...">
                if element.name == 'meta':
                    if element.has_attribute(None, 'http-equiv'):
                        value = element.get_attribute(None, 'http-equiv')
                        if value == 'Content-Type':
                            continue

                if stack:
                    stack[-1].set_element(element)
                else:
                    children.append(element)
            elif event == COMMENT:
                comment = Comment(value)
                if stack:
                    stack[-1].set_comment(comment)
                else:
                    children.append(comment)
            elif event == TEXT:
                if stack:
                    stack[-1].set_text(value, parser.encoding)
                else:
                    value = Unicode.decode(value, parser.encoding)
                    children.append(value)

        # Semantically, the root of an HTML document is always the "<html>"
        # element.
        for element in children:
            if isinstance(element, Element) and element.name == 'html':
                self.root_element = element
                # XXX We loss any comment or text node that is before or
                # after the "<html>" tag.
                break
        else:
            schema = elements_schema.get('html', {'type': Element,
                                                  'is_inline': False})
            element_class = schema['type']
            element = element_class('html')
            element.children = children
            self.root_element = element


    def header_to_str(self, encoding='UTF-8'):
        if self.document_type is None:
            return ''
        return '<!%s>' % self.document_type


register_handler_class(Document)
