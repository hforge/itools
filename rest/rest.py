# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
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

# Import from the Standard Library
import cgi

# Import from itools
from itools.handlers import register_handler_class
from itools.xml import (Document as XMLDocument, AbstractNamespace,
        set_namespace, stream_to_str as stream_to_str_as_xml, TEXT, COMMENT,
        START_ELEMENT, END_ELEMENT)
from itools.datatypes import Unicode
from itools.schemas import Schema as BaseSchema, register_schema

# Import from itools.cms
from itools.cms.utils import checkid

# Import from rest
from parser import Document as RestDocument, parse_inline


# XXX dummy
rest_uri = 'http://docutils.sourceforge.net/docs/ref/docutils.dtd'


def block_stream(text):
    events = []

    for event, value in RestDocument(text):
        if event == 'title':
            overline, title, underline = value
            target = checkid(title).lower()
            attributes = {(rest_uri, 'overline'): overline,
                          (rest_uri, 'underline'): underline,
                          (rest_uri, 'target'): target}
            events.append((START_ELEMENT, (rest_uri, event, attributes)))
            events.extend(inline_stream(title))
            events.append((END_ELEMENT, (rest_uri, event)))
        elif event == 'paragraph':
            events.append((START_ELEMENT, (rest_uri, event, {})))
            events.extend(inline_stream(value))
            events.append((END_ELEMENT, (rest_uri, event)))
        elif event == 'literal_block':
            events.append((START_ELEMENT, (rest_uri, event, {})))
            events.append((TEXT, value))
            events.append((END_ELEMENT, (rest_uri, event)))
        elif event == 'list_begin':
            events.append((START_ELEMENT, (rest_uri, event,
                {(rest_uri, 'item'): value})))
        elif event == 'list_end':
            events.append((END_ELEMENT, (rest_uri, event)))
        elif event == 'list_item_begin':
            events.append((START_ELEMENT, (rest_uri, 'list_item', {})))
        elif event == 'list_item_end':
            events.append((END_ELEMENT, (rest_uri, 'list_item')))
        else:
            raise NotImplementedError, event

    return events


def inline_stream(text):
    events = []

    for event, value in parse_inline(text):
        if event == 'text':
            events.append((TEXT, value))
        elif event == 'footnote':
            target = checkid(value).lower()
            attributes = {'target': target}
            events.append((START_ELEMENT, (rest_uri, event, attributes)))
            events.append((TEXT, value))
            events.append((END_ELEMENT, (rest_uri, event)))
        elif event == 'reference':
            target = checkid(value).lower()
            attributes = {'target': target}
            events.append((START_ELEMENT, (rest_uri, event, attributes)))
            events.append((TEXT, value))
            events.append((END_ELEMENT, (rest_uri, event)))
        else:
            events.append((START_ELEMENT, (rest_uri, event, {})))
            events.append((TEXT, value))
            events.append((END_ELEMENT, (rest_uri, event)))

    return events


def stream_to_str(stream, encoding='UTF-8'):
    raise NotImplementedError


def stream_to_str_as_html(stream, encoding='UTF-8'):
    buffer = []
    title_levels = []
    last_title_level = None
    list_items = []
    one_to_one = {'paragraph': 'p',
                  'literal_block': 'pre',
                  'list_item': 'li',
                  'strong': 'strong',
                  'emphasis': 'em',
                  'literal': 'tt'}

    for event, value in stream:
        if event == TEXT:
            data = Unicode.encode(value, encoding)
            data = cgi.escape(data)
            buffer.append(data)
        elif event == START_ELEMENT:
            _, name, attributes = value
            if name == 'title':
                overline = attributes[(rest_uri, 'overline')]
                underline = attributes[(rest_uri, 'underline')]
                if (overline, underline) in title_levels:
                    level = title_levels.index((overline, underline))
                else:
                    level = len(title_levels)
                    title_levels.append((overline, underline))
                # Anchor to this section
                target = attributes[(rest_uri, 'target')]
                buffer.append('<a name="%s"></a>' % target)
                # index 0 -> <h1>
                level += 1
                buffer.append('<h%d>' % level)
                last_title_level = level
            elif name == 'footnote':
                target = str(attributes['target'])
                buffer.append('<a href="#id%s">[' % target)
            elif name == 'reference':
                target = attributes['target']
                buffer.append('<a href="#%s">' % target)
            elif name == 'list_begin':
                item = attributes[(rest_uri, 'item')]
                if item == u'#':
                    buffer.append('<ol>')
                else:
                    buffer.append('<ul>')
                list_items.append(item)
            elif name in ('document',):
                pass
            else:
                tag = one_to_one[name]
                buffer.append('<%s>' % tag)
        elif event == END_ELEMENT:
            _, name = value
            if name == 'title':
                buffer.append('</h%d>' % last_title_level)
            elif name == 'footnote':
                buffer.append(']</a>')
            elif name == 'reference':
                buffer.append('</a>')
            elif name == 'list_end':
                if list_items.pop() == u'#':
                    buffer.append('</ol>')
                else:
                    buffer.append('</ul>')
            elif name in ('document',):
                pass
            else:
                tag = one_to_one[name]
                buffer.append('</%s>' % tag)

    return ''.join(buffer)



class RestNamespace(AbstractNamespace):

    class_uri = rest_uri
    class_prefix = None

    @staticmethod
    def get_element_schema(name):
        return {'is_empty': False}


set_namespace(RestNamespace)



class RestSchema(BaseSchema):

    class_uri = rest_uri
    class_prefix = None

    @classmethod
    def get_datatype(cls, name):
        return Unicode


register_schema(RestSchema)



class Document(XMLDocument):
    """
    Handler of reStructuredText files.
    See http://docutils.sourceforge.net/rst.html

    The reST handler is technically a Text handler but offering the XML API.
    """

    class_mimetypes = ['text/x-rst', 'text/x-restructured-text']
    class_extension = 'rst'

    def _load_state_from_file(self, file):
        data = file.read()
        encoding = self.guess_encoding(data)
        text = unicode(data, encoding)
        del data

        events = []
        events.append((START_ELEMENT, (rest_uri, 'document', {})))
        events.extend(block_stream(text))
        events.append((END_ELEMENT, (rest_uri, 'document')))
        self.events = events


    def header_to_str(self, encoding='UTF-8'):
        # No sense in reST
        raise NotImplementedError


    def get_content_as_html(self, encoding='UTF-8'):
        return stream_to_str_as_html(self.events, encoding)


    def get_content_as_xml(self, encoding='UTF-8'):
        return stream_to_str_as_xml(self.events, encoding)


    def to_str(self, encoding='UTF-8'):
        """
        Re-generate a reST text file.
        """
        return stream_to_str(self.events, encoding)


    def to_xml(self, encoding='UTF-8'):
        """
        Generate the XML representation of the document tree.
        """
        s = ['<?xml version="1.0" encoding="%s"?>\n'
             '<!DOCTYPE document PUBLIC\n'
             '    +//IDN docutils.sourceforge.net//DTD Docutils Generic//EN//XML"\n'
             '    http://docutils.sourceforge.net/docs/ref/docutils.dtd">' % encoding]
        s.append(stream_to_str_as_xml(self.events, encoding))
        return '\n'.join(s)


    def to_html(self, encoding='UTF-8'):
        """
        Translate the document to XHTML.
        """
        title = self.get_element('title').get_content()
        mapping = {'title': title,
                   'encoding': encoding}
        s = ['<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
             '       "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
             '<html xmlns="http://www.w3.org/1999/xhtml">\n'
             '  <head>\n'
             '    <meta http-equiv="Content-Type" content="text/html; charset=%(encoding)s" />\n'
             '    <title>%(title)s</title>\n'
             '  </head>\n'
             '  <body>' % mapping]
        s.append(self.get_content_as_html(encoding))
        s.append(    '</body>\n'
                 '</html>')
        return '\n'.join(s)


register_handler_class(Document)
