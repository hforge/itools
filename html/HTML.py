# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.datatypes import Unicode
from itools.handlers import File
from itools.handlers.registry import register_handler_class
from itools.xml import XML
from itools.xhtml import XHTML
from itools.html.parser import Parser, DOCUMENT_TYPE, START_ELEMENT, \
     END_ELEMENT, COMMENT, TEXT



class Element(XHTML.Element):

    get_start_tag = XHTML.Element.get_start_tag_as_html


class InlineElement(Element, XHTML.InlineElement):
    pass


class BlockElement(Element, XHTML.BlockElement):
    pass


# XXX This class is almost identical to 'XHTML.Element'
class HeadElement(BlockElement):

    def to_str(self, encoding='UTF-8'):
        head = []
        head.append('<head>\n')
        head.append('    <meta http-equiv="Content-Type" content="text/html; charset=%s" />\n' % encoding)
        head.append(self.get_content(encoding))
        head.append('</head>')
        return ''.join(head)


elements_schema = {
    'a': {'type': InlineElement},
    'abbr': {'type': InlineElement},
    'acronym': {'type': InlineElement},
    'b': {'type': InlineElement},
    'cite': {'type': InlineElement},
    'code': {'type': InlineElement},
    'dfn': {'type': InlineElement},
    'em': {'type': InlineElement},
    'head': {'type': HeadElement},
    'kbd': {'type': InlineElement},
    'q': {'type': InlineElement},
    'samp': {'type': InlineElement},
    'span': {'type': InlineElement},
    'strong': {'type': InlineElement},
    'sub': {'type': InlineElement},
    'sup': {'type': InlineElement},
    'tt': {'type': InlineElement},
    'var': {'type': InlineElement},
    }


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


    #######################################################################
    # Load/Save
    #######################################################################
    def load_state_from_file(self, file):
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
                schema = elements_schema.get(name, {'type': BlockElement})
                element_class = schema['type']
                element = element_class(name)
                for attr_name in attributes:
                    attr_value = attributes[attr_name]
                    element.set_attribute(None, attr_name, attr_value)
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
                comment = XML.Comment(value)
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
            schema = elements_schema.get('html', {'type': BlockElement})
            element_class = schema['type']
            element = element_class('html')
            element.children = children
            self.root_element = element


    def to_str(self, encoding='UTF-8'):
        data = []
        # The declaration
        if self.document_type is not None:
            data.append('<!%s>' % self.document_type)
        # The document itself
        data.append(self.get_root_element().to_str(encoding))

        return ''.join(data)


register_handler_class(Document)
