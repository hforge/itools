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


# Import from itools
from itools.handlers import File, IO
from itools.xml import XML
from itools.xhtml import XHTML
from itools.html import parser



class Element(XHTML.Element):

    def get_closetag(self):
        if self.name in parser.empty_elements:
            return ''
        return XHTML.Element.get_closetag(self)


# XXX This class is almost identical to 'XHTML.Element'
class HeadElement(Element):

    def to_unicode(self, encoding='UTF-8'):
        return ''.join([self.get_opentag(),
                        '\n    <meta http-equiv="Content-Type" content="text/html; charset=%s">' % encoding,
                        XML.Children.to_unicode(self.children,
                                                encoding=encoding),
                        self.get_closetag()])


    def set_element(self, element):
        # Skip content type declaration
        if element.name == 'meta':
            if element.has_attribute(None, 'http-equiv'):
                value = element.get_attribute(None, 'http-equiv')
                if value == 'Content-Type':
                    return
        self.children.append(element)




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
        self._encoding = 'UTF-8'
        self.document_type = None
        self.children = []

        stack = []
        data = resource.read()
        for event, value, line_number in parser.Parser().parse(data):
            if event == parser.DOCUMENT_TYPE:
                self.document_type = value
            elif event == parser.START_ELEMENT:
                stack.append(Element(None, value))
            elif event == parser.END_ELEMENT:
                element = stack.pop()
                if stack:
                    stack[-1].set_element(element)
                else:
                    self.children.append(element)
            elif event == parser.ATTRIBUTE:
                name, value = value
                type = IO.Unicode
                value = type.decode(value, self._encoding)
                stack[-1].set_attribute(None, name, value)
            elif event == parser.COMMENT:
                comment = XML.Comment(value)
                if stack:
                    stack[-1].set_comment(comment)
                else:
                    self.children.append(comment)
            elif event == parser.TEXT:
                if stack:
                    stack[-1].set_text(value, self._encoding)
                else:
                    value = IO.Unicode.decode(value, self._encoding)
                    self.children.append(value)


    def to_unicode(self, encoding='UTF-8'):
        s = u''
        # The declaration
        if self.document_type is not None:
            s = u'<!%s>' % self.document_type
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
        if self.document_type is not None:
            s = u'<!%s>' % self.document_type
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
