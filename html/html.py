# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.xhtml import (Document as XHTMLDocument, xhtml_uri,
                          stream_to_str_as_html, elements_schema)
from parser import (Parser, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT,
                    COMMENT, TEXT)



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
                 'document_type', 'events', 'encoding']


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
        data = [self.header_to_str(encoding),
                stream_to_str_as_html(self.events, encoding)]

        return ''.join(data)


    #######################################################################
    # Load/Save
    #######################################################################
    def _load_state_from_file(self, file):
        self.encoding = 'UTF-8'
        self.document_type = None

        data = file.read()
        parser = Parser()
        events = []
        for event, value, line_number in parser.parse(data):
            if event == DOCUMENT_TYPE:
                self.document_type = value
            elif event == TEXT:
                value = unicode(value, parser.encoding)
                events.append((event, value))
            elif event == START_ELEMENT:
                name, attributes = value
                schema = elements_schema.get(name, {'is_inline': False})
                aux = {}
                for attr_name in attributes:
                    attr_value = attributes[attr_name]
                    type = get_datatype_by_uri(xhtml_uri, attr_name)
                    aux[(xhtml_uri, attr_name)] = type.decode(attr_value)
                events.append((event, (xhtml_uri, name, aux)))
            else:
                events.append((event, value))

        self.events = events


    def header_to_str(self, encoding='UTF-8'):
        if self.document_type is None:
            return ''
        return '<!%s>' % self.document_type


register_handler_class(Document)
