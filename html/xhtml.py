# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from the Standard Library
from re import finditer
from cStringIO import StringIO

# Import from itools
from itools.datatypes import XMLContent, XMLAttribute
from itools.handlers import register_handler_class
from itools.xml import XMLParser, XML_DECL, DOCUMENT_TYPE, START_ELEMENT
from itools.xml import END_ELEMENT, TEXT, COMMENT
from itools.xml import stream_to_str, get_qname, get_attribute_qname
from itools.xml import get_end_tag, get_doctype
from itools.xml import XMLFile, get_element


xhtml_uri = 'http://www.w3.org/1999/xhtml'



def stream_to_html(stream, encoding='UTF-8'):
    data = []
    for event in stream:
        type, value, line = event
        if type == TEXT:
            value = XMLContent.encode(value)
            data.append(value)
        elif type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            qname = get_qname(tag_uri, tag_name)
            s = '<%s' % qname
            # Output the attributes
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                qname = get_attribute_qname(attr_uri, attr_name)
                value = XMLAttribute.encode(value)
                s += ' %s="%s"' % (qname, value)
            data.append(s + '>')
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            data.append(get_end_tag(tag_uri, tag_name))
        elif type == COMMENT:
            data.append('<!--%s-->' % value)
        elif type == XML_DECL:
            pass
        elif type == DOCUMENT_TYPE:
            name, doctype = value
            data.append(get_doctype(name, doctype))
    return ''.join(data)


def set_content_type(stream, content_type):
    key1 = (None, 'http-equiv')
    key2 = (None, 'content')
    for event in stream:
        type, value, line = event
        if type == START_ELEMENT:
            ns_uri, name, attributes = value
            if ns_uri == xhtml_uri:
                # Skip <meta http-equiv="Content-Type">
                if name == 'meta':
                    if key1 in attributes:
                        if attributes[key1] == 'Content-Type':
                            continue
                elif name == 'head':
                    yield event
                    # Add <meta http-equiv="Content-Type">
                    attributes = {}
                    attributes[key1] = 'Content-Type'
                    attributes[key2] = content_type
                    yield START_ELEMENT, (None, 'meta', attributes), line
                    yield END_ELEMENT, (None, 'meta'), line
                    continue
        elif type == END_ELEMENT:
            ns_uri, name = value
            if ns_uri == xhtml_uri:
                # Skip <meta http-equiv="Content-Type">
                if name == 'meta':
                    # XXX This will fail if there is another element
                    # within the "<meta>" element (something that should
                    # not happen).
                    if key1 in attributes:
                        if attributes[key1] == 'Content-Type':
                            continue
        yield event


def stream_to_str_as_xhtml(stream, encoding='UTF-8'):
    content_type = 'application/xhtml+xml; charset=%s' % encoding
    stream = set_content_type(stream, content_type)
    return stream_to_str(stream, encoding)



def stream_to_str_as_html(stream, encoding='UTF-8'):
    content_type = 'text/html; charset=%s' % encoding
    stream = set_content_type(stream, content_type)
    return stream_to_html(stream, encoding)


def sanitize_stream(stream):
    """Method that removes potentially dangerous HTML tags and attributes
    from the events
    """
    safe_tags = frozenset(['a', 'abbr', 'acronym', 'address', 'area',
        'b', 'big', 'blockquote', 'br', 'button', 'caption', 'center',
        'cite', 'code', 'col', 'colgroup', 'dd', 'del', 'dfn', 'dir',
        'div', 'dl', 'dt', 'em', 'fieldset', 'font', 'form', 'h1', 'h2',
        'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'input', 'ins', 'kbd',
        'label', 'legend', 'li', 'map', 'menu', 'ol', 'optgroup',
        'option', 'p', 'pre', 'q', 's', 'samp', 'select', 'small',
        'span', 'strike', 'strong', 'sub', 'sup', 'table', 'tbody',
        'td', 'textarea', 'tfoot', 'th', 'thead', 'tr', 'tt', 'u', 'ul',
        'var'])

    safe_attrs = frozenset(['abbr', 'accept', 'accept-charset',
        'accesskey', 'action', 'align', 'alt', 'axis', 'border',
        'cellpadding', 'cellspacing', 'char', 'charoff', 'charset',
        'checked', 'cite', 'class', 'clear', 'cols', 'colspan', 'color',
        'compact', 'coords', 'datetime', 'dir', 'disabled', 'enctype',
        'for', 'frame', 'headers', 'height', 'href', 'hreflang',
        'hspace', 'id', 'ismap', 'label', 'lang', 'longdesc',
        'maxlength', 'media', 'method', 'multiple', 'name', 'nohref',
        'noshade', 'nowrap', 'prompt', 'readonly', 'rel', 'rev', 'rows',
        'rowspan', 'rules', 'scope', 'selected', 'shape', 'size',
        'span', 'src', 'start', 'style', 'summary', 'tabindex',
        'target', 'title', 'type', 'usemap', 'valign', 'value',
        'vspace', 'width'])

    safe_schemes = frozenset(['file', 'ftp', 'http', 'https', 'mailto', None])

    uri_attrs = frozenset(['action', 'background', 'dynsrc', 'href', 'lowsrc',
                           'src'])

    events_to_remove = []
    events = list(stream)
    remove_next = False
    for c_event in events:
        event, value, line = c_event
        if event == START_ELEMENT:
            _, name, attributes = value
            # Remove unsafe Tag
            if name not in safe_tags:
                events_to_remove.append(c_event)
                # Remove until end tad
                remove_next = True
                continue
            # Remove unsafe attributes
            attributes_to_remove = []
            for c_attribute in attributes:
                attr_uri, attr_name = c_attribute
                # Remove unauthorized attributes
                if attr_name not in safe_attrs:
                    attributes_to_remove.append(c_attribute)
                # Check attributes with Uri
                if attr_name in uri_attrs:
                    href = attributes[c_attribute]
                    if ':' in href:
                        scheme = href.split(':')[0]
                        if scheme not in safe_schemes:
                            attributes_to_remove.append(c_attribute)
                # Check CSS
                if attr_name in 'style':
                    value = attributes[c_attribute]
                    for m in finditer(r'url\s*\(([^)]+)', value):
                        href = m.group(1)
                        if ':' in href:
                            scheme = href.split(':')[0]
                            if scheme not in safe_schemes:
                                attributes_to_remove.append(c_attribute)
            for attr_to_remove in attributes_to_remove:
                attributes.pop(attr_to_remove)
        elif event == END_ELEMENT:
            _, name = value
            if name not in safe_tags:
                events_to_remove.append(c_event)
                remove_next = False
                continue
        elif event == COMMENT:
            events_to_remove.append(c_event)
            continue
        if remove_next==True:
            events_to_remove.append(c_event)
    # Remove unsafe events
    for event_to_remove in events_to_remove:
        events.remove(event_to_remove)
    return events


def sanitize_str(str):
    stream = XMLParser(str)
    events = sanitize_stream(stream)
    return events



#############################################################################
# Document
#############################################################################
class XHTMLFile(XMLFile):
    """This class adds one thing to the XML class, the semantics of
    translatable text.
    """

    class_mimetypes = ['application/xhtml+xml']
    class_extension = 'xhtml'

    namespace = xhtml_uri

    #########################################################################
    # The skeleton
    #########################################################################
    def new(self, title=''):
        skeleton = self.get_skeleton(title)
        file = StringIO()
        file.write(skeleton)
        file.seek(0)
        self.load_state_from_file(file)


    @classmethod
    def get_skeleton(cls, title=''):
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
            '  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml">\n'
            '  <head>\n'
            '    <meta http-equiv="Content-Type" content="text/html; '
            'charset=UTF-8" />\n'
            '    <title>%(title)s</title>\n'
            '  </head>\n'
            '  <body></body>\n'
            '</html>')
        return data % {'title': title}


    def to_xhtml(self, encoding='utf-8'):
        return stream_to_str_as_xhtml(self.events, encoding)


    def to_html(self, encoding='utf-8'):
        return stream_to_str_as_html(self.events, encoding)


    to_str = to_xhtml


    ########################################################################
    # API
    ########################################################################
    def get_head(self):
        """Returns the head element.
        """
        return get_element(self.events, 'head')


    def get_body(self):
        """Returns the body element.
        """
        return get_element(self.events, 'body')


    def get_body_as_html(self):
        body = self.get_body()
        if body is None:
            return None
        return stream_to_str_as_html(body.get_content_elements())


    def set_body(self, events):
        body = self.get_body()
        events = self.events[:body.start+1] + events + self.events[body.end:]
        self.set_changed()
        self.events = events


register_handler_class(XHTMLFile)
