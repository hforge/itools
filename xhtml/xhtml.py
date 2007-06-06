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

# Import from the Standard Library
import re
from cStringIO import StringIO

# Import from itools
from itools.datatypes import (Boolean, Integer, Unicode, String, URI,
    XML as XMLDataType, XMLAttribute)
from itools.schemas import (Schema as BaseSchema, get_datatype_by_uri,
    register_schema)
from itools.handlers import register_handler_class
from itools.xml import (Document as XMLDocument, XML_DECL, DOCUMENT_TYPE,
    START_ELEMENT, END_ELEMENT, TEXT, COMMENT, AbstractNamespace,
    set_namespace, stream_to_str, get_qname, get_attribute_qname, is_empty,
    get_end_tag, get_element)


xhtml_uri = 'http://www.w3.org/1999/xhtml'


#############################################################################
# Types
#############################################################################

class Boolean(Boolean):

    @staticmethod
    def decode(value):
        return value


    @staticmethod
    def encode(value):
        return value



def stream_to_html(stream, encoding='UTF-8'):
    data = []
    for event in stream:
        type, value, line = event
        if type == TEXT:
            data.append(value)
        elif type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            qname = get_qname(tag_uri, tag_name)
            s = '<%s' % qname
            # Output the attributes
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                qname = get_attribute_qname(attr_uri, attr_name)
                type = get_datatype_by_uri(attr_uri, attr_name)
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
            # FIXME
            pass
    return ''.join(data)


def set_content_type(stream, content_type):
    key1 = (xhtml_uri, 'http-equiv')
    key2 = (xhtml_uri, 'content')
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
                    yield START_ELEMENT, (xhtml_uri, 'meta', attributes), line
                    yield END_ELEMENT, (xhtml_uri, 'meta'), line
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


#############################################################################
# Namespace
#############################################################################

elements_schema = {
    # XHTML 1.0 strict
    'a': {'is_empty': False, 'is_inline': True},
    'abbr': {'is_empty': False, 'is_inline': True},
    'acronym': {'is_empty': False, 'is_inline': True},
    'area': {'is_empty': True, 'is_inline': False},
    'b': {'is_empty': False, 'is_inline': True},
    'base': {'is_empty': True, 'is_inline': False},
    'bdo': {'is_empty': False, 'is_inline': True},
    'big': {'is_empty': False, 'is_inline': True},
    'br': {'is_empty': True, 'is_inline': True},
    'cite': {'is_empty': False, 'is_inline': True},
    'code': {'is_empty': False, 'is_inline': True},
    'col': {'is_empty': True, 'is_inline': False},
    'dfn': {'is_empty': False, 'is_inline': True},
    'em': {'is_empty': False, 'is_inline': True},
    'head': {'is_empty': False, 'is_inline': False},
    'hr': {'is_empty': True, 'is_inline': False},
    'i': {'is_empty': False, 'is_inline': True},
    'img': {'is_empty': True, 'is_inline': True},
    'input': {'is_empty': True, 'is_inline': True},
    'kbd': {'is_empty': False, 'is_inline': True},
    'link': {'is_empty': True, 'is_inline': False},
    'meta': {'is_empty': True, 'is_inline': False},
    'param': {'is_empty': True, 'is_inline': False},
    'q': {'is_empty': False, 'is_inline': True},
    'samp': {'is_empty': False, 'is_inline': True},
    # FIXME This is a lie, <select> elements *are* inline
    # TODO Do not use the inline/block for i18n, define instead another
    # variable for this purpose.
    'select': {'is_empty': False, 'is_inline': False},
    'small': {'is_empty': False, 'is_inline': True},
    'span': {'is_empty': False, 'is_inline': True},
    'strong': {'is_empty': False, 'is_inline': True},
    'sub': {'is_empty': False, 'is_inline': True},
    'sup': {'is_empty': False, 'is_inline': True},
    'textarea': {'is_empty': False, 'is_inline': True},
    'tt': {'is_empty': False, 'is_inline': True},
    'var': {'is_empty': False, 'is_inline': True},
    # XHTML 1.0 transitional
    'basefont': {'is_empty': True, 'is_inline': True},
    'font': {'is_empty': False, 'is_inline': True},
    'isindex': {'is_empty': True, 'is_inline': False},
    's': {'is_empty': False, 'is_inline': True},
    'strike': {'is_empty': False, 'is_inline': True},
    'u': {'is_empty': False, 'is_inline': True},
    # XHTML 1.0 frameset
    'frame': {'is_empty': True, 'is_inline': False},
    # Vendor specific, not approved by W3C
    'embed': {'is_empty': True, 'is_inline': False},
    # Unclassified
    'script': {'is_empty': False, 'is_inline': False,
        'translate_content': False},
    'style': {'is_empty': False, 'is_inline': False,
        'translate_content': False},
    }


class Namespace(AbstractNamespace):

    class_uri = xhtml_uri
    class_prefix = None


    @staticmethod
    def get_element_schema(name):
        default_schema = {'is_empty': False, 'is_inline': False}
        return elements_schema.get(name, default_schema)


    @classmethod
    def is_translatable(cls, tag_uri, tag_name, attributes, attribute_name):
        # Attributes
        if attribute_name == 'title':
            return True
        if tag_name == 'img' and attribute_name == 'alt':
            return True
        if tag_name == 'input' and attribute_name == 'value':
            value = attributes.get((cls.class_uri, 'type'))
            return value == 'submit'
        return False


set_namespace(Namespace)



class Schema(BaseSchema):

    class_uri = xhtml_uri
    class_prefix = None

    datatypes = {'abbr': Unicode,
                 'accept-charsert': String,
                 'accept': String,
                 'accesskey': Unicode,
                 'action': URI,
                 'align': String,
                 'alink': String,
                 'alt': Unicode,
                 'archive': Unicode,
                 'axis': Unicode,
                 'background': URI,
                 'bgcolor': String,
                 'border': Integer,
                 # XXX Check, http://www.w3.org/TR/html4/index/attributes.html
                 'cellpadding': Unicode,
                 'cellspacing': Unicode,
                 'char': Unicode,
                 'charoff': Unicode,
                 'charset': Unicode,
                 'checked': Boolean,
                 'cite': Unicode,
                 'class': Unicode,
                 'classid': Unicode,
                 'clear': Unicode,
                 'code': Unicode,
                 'codebase': Unicode,
                 'codetype': Unicode,
                 'color': Unicode,
                 'cols': Unicode,
                 'colspan': Unicode,
                 'compact': Boolean,
                 'content': Unicode,
                 'coords': Unicode,
                 'data': Unicode,
                 'datetime': Unicode,
                 'declare': Boolean,
                 'defer': Boolean,
                 'dir': Unicode,
                 'disabled': Boolean,
                 'enctype': Unicode,
                 'face': Unicode,
                 'for': Unicode,
                 'frame': Unicode,
                 'frameborder': Unicode,
                 'headers': Unicode,
                 'height': Unicode,
                 # XXX This should be of type URI, but it produces an error
                 # with the STL substitution syntax, because the query
                 # escapes the characters "$", "{" and "}".
                 'href': String,
                 'hreflang': Unicode,
                 'hspace': Unicode,
                 'http-equiv': Unicode,
                 'id': Unicode,
                 'ismap': Boolean,
                 'label': Unicode,
                 'lang': Unicode,
                 'language': Unicode,
                 'link': Unicode,
                 'longdesc': Unicode,
                 'marginheight': Unicode,
                 'marginwidth': Unicode,
                 'media': Unicode,
                 'method': Unicode,
                 'multiple': Boolean,
                 'name': Unicode,
                 'nohref': Unicode,
                 'noresize': Boolean,
                 'noshade': Boolean,
                 'nowrap': Boolean,
                 'object': Unicode,
                 'onblur': Unicode,
                 'onchange': Unicode,
                 'onclick': Unicode,
                 'ondblclick': Unicode,
                 'onfocus': Unicode,
                 'onkeydown': Unicode,
                 'onkeypress': Unicode,
                 'onkeyup': Unicode,
                 'onload': Unicode,
                 'onmousedown': Unicode,
                 'onmousemove': Unicode,
                 'onmouseout': Unicode,
                 'onmouseover': Unicode,
                 'onmouseup': Unicode,
                 'onreset': Unicode,
                 'onselect': Unicode,
                 'onsubmit': Unicode,
                 'onunload': Unicode,
                 'profile': Unicode,
                 'prompt': Unicode,
                 'readonly': Boolean,
                 'rel': Unicode,
                 'rev': Unicode,
                 'rows': Unicode,
                 'rowspan': Unicode,
                 'rules': Unicode,
                 'scheme': Unicode,
                 'scope': Unicode,
                 'scrolling': Unicode,
                 'selected': Boolean,
                 'shape': Unicode,
                 'size': Unicode,
                 'span': Unicode,
                 'src': URI,
                 'standby': Unicode,
                 'start': Unicode,
                 'style': Unicode,
                 'summary': Unicode,
                 'tabindex': Unicode,
                 'target': Unicode,
                 'text': Unicode,
                 'title': Unicode,
                 'type': Unicode,
                 'usemap': Unicode,
                 'valign': Unicode,
                 'value': Unicode,
                 'valuetype': Unicode,
                 'version': Unicode,
                 'vlink': Unicode,
                 'vspace': Unicode,
                 'width': Unicode,
                 }


    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

register_schema(Schema)



#############################################################################
# Document
#############################################################################
class Document(XMLDocument):
    """
    This class adds one thing to the XML class, the semantics of translatable
    text.
    """

    class_mimetypes = ['application/xhtml+xml']
    class_extension = 'xhtml'

    namespace = xhtml_uri

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'events']


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
            '    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
            '    <title>%(title)s</title>\n'
            '  </head>\n'
            '  <body></body>\n'
            '</html>')
        return data % {'title': title}


    def to_str(self, encoding='UTF-8'):
        return stream_to_str_as_xhtml(self.events, encoding)


    ########################################################################
    # API
    ########################################################################
    def get_head(self):
        """Returns the head element."""
        return get_element(self.events, 'head')


    def get_body(self):
        """Returns the body element."""
        return get_element(self.events, 'body')


register_handler_class(Document)
