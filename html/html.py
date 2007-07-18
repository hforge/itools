# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.handlers import register_handler_class
from itools.xml import translate
from itools.xhtml import Document as XHTMLDocument, stream_to_str_as_html
from parser import Parser



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
                 'events', 'encoding']


    @classmethod
    def get_skeleton(cls, title=''):
        skeleton = (
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n'
            '  "http://www.w3.org/TR/html4/loose.dtd">\n'
            '<html>\n'
            '  <head>\n'
            '    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'
            '    <title>%(title)s</title>\n'
            '  </head>\n'
            '  <body></body>\n'
            '</html>')
        return skeleton % {'title': title}


    def _load_state_from_file(self, file):
        self.encoding = 'UTF-8'
        data = file.read()
        stream = Parser(data)
        self.events = list(stream)

    to_str = XHTMLDocument.to_html


    #######################################################################
    # API
    #######################################################################
    def translate(self, catalog):
        stream = translate(self.events, catalog)
        return stream_to_str_as_html(stream)


register_handler_class(Document)
