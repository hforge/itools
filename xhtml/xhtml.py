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
from itools.xml import (Document as XMLDocument, Element, 
                        START_ELEMENT, END_ELEMENT, TEXT, COMMENT,
                        AbstractNamespace, set_namespace, get_namespace,
                        get_element_schema, filter_root_stream, stream_to_str,
                        get_qname, get_attribute_qname, is_empty, get_end_tag)
from itools.i18n import Message


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
    for event, value in stream:
        if event == TEXT:
            value = value.encode(encoding)
            data.append(value)
        elif event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            qname = get_qname(tag_uri, tag_name)
            s = '<%s' % qname
            # Output the attributes
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                qname = get_attribute_qname(attr_uri, attr_name)
                type = get_datatype_by_uri(attr_uri, attr_name)
                value = type.encode(value)
                value = XMLAttribute.encode(value)
                s += ' %s="%s"' % (qname, value)
            data.append(s + '>')
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            data.append(get_end_tag(tag_uri, tag_name))
        elif event == COMMENT:
            value = value.encode(encoding)
            data.append('<!--%s-->' % value)
        else:
            raise NotImplementedError, str(event)
    return ''.join(data)



def stream_to_str_as_xhtml(stream, encoding='UTF-8'):
    # This method is almost identical to Element.to_str, but we must
    # override it to be sure the document has the correct encoding set
    # (<meta http-equiv="Content-Type" content="...">)

    def filter(stream, encoding):
        key1 = (xhtml_uri, 'http-equiv')
        key2 = (xhtml_uri, 'content')
        key2_value = 'application/xhtml+xml; charset=%s'
        for event, value in stream:
            if event == START_ELEMENT:
                ns_uri, name, attributes = value
                if ns_uri == xhtml_uri:
                    # Skip <meta http-equiv="Content-Type">
                    if name == 'meta':
                        if key1 in attributes:
                            if attributes[key1] == 'Content-Type':
                                continue
                    elif name == 'head':
                        yield event, value
                        # Add <meta http-equiv="Content-Type">
                        attributes = {}
                        attributes[key1] = 'Content-Type'
                        attributes[key2] = key2_value % encoding
                        yield START_ELEMENT, (xhtml_uri, 'meta', attributes)
                        yield END_ELEMENT, (xhtml_uri, 'meta')
                        continue
            elif event == END_ELEMENT:
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
            yield event, value

    return stream_to_str(filter(stream, encoding), encoding)



def stream_to_str_as_html(stream, encoding='UTF-8'):
    def filter(stream, encoding):
        key1 = (xhtml_uri, 'http-equiv')
        key2 = (xhtml_uri, 'content')
        key2_value = 'text/html; charset=%s'
        for event, value in stream:
            if event == START_ELEMENT:
                ns_uri, name, attributes = value
                if ns_uri == xhtml_uri:
                    # Skip <meta http-equiv="Content-Type">
                    if name == 'meta':
                        if key1 in attributes:
                            if attributes[key1] == 'Content-Type':
                                continue
                    elif name == 'head':
                        yield event, value
                        # Add <meta http-equiv="Content-Type">
                        attributes = {}
                        attributes[key1] = 'Content-Type'
                        attributes[key2] = key2_value % encoding
                        yield START_ELEMENT, (xhtml_uri, 'meta', attributes)
                        yield END_ELEMENT, (xhtml_uri, 'meta')
                        continue
            elif event == END_ELEMENT:
                ns_uri, name = value
                if ns_uri == xhtml_uri:
                    # Skip <meta http-equiv="Content-Type">
                    if name == 'meta':
                        if key1 in attributes:
                            if attributes[key1] == 'Content-Type':
                                continue

            yield event, value

    return stream_to_html(filter(stream, encoding), encoding)


def element_content_to_html(element, encoding='UTF-8'):
    return stream_to_html(filter_root_stream(element), encoding)



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
    'select': {'is_empty': False, 'is_inline': True},
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
def open_tag(tag_uri, tag_name, attributes, buffer, catalog):
    # The open tag
    qname = get_qname(tag_uri, tag_name)
    buffer.write('<%s' % qname)
    # The attributes
    for attr_uri, attr_name in attributes:
        value = attributes[(attr_uri, attr_name)]
        namespace = get_namespace(attr_uri)
        if namespace.is_translatable(tag_uri, tag_name, attributes, attr_name):
            value = value.strip()
            if value:
                value = catalog.get_translation(value)
                #value = catalog.get_msgstr(value) or value
        qname = get_attribute_qname(attr_uri, attr_name)
        datatype = get_datatype_by_uri(attr_uri, attr_name)
        value = datatype.encode(value)
        value = XMLAttribute.encode(value)
        buffer.write(' %s="%s"' % (qname, value))
    # Close the start tag
    if is_empty(tag_uri, tag_name):
        buffer.write('/>')
    else:
        buffer.write('>')


def normalize(message):
    """
    Concatenates adjacent text nodes.
    """
    i = 0
    while i < len(message) - 1:
        this, next = message[i], message[i+1]
        if this[0] == TEXT and next[0] == TEXT:
            message[i] = (TEXT, this[1] + next[1])
            del message[i+1]
        else:
            i = i + 1


class Document(XMLDocument):
    """
    This class adds one thing to the XML class, the semantics of translatable
    text.
    """

    class_mimetypes = ['application/xhtml+xml']
    class_extension = 'xhtml'

    namespace = xhtml_uri

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'document_type', 'events']


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
        data = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n'
                '       "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
                '<html xmlns="http://www.w3.org/1999/xhtml">\n'
                '  <head>\n'
                '    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n'
                '    <title>%(title)s</title>\n'
                '  </head>\n'
                '  <body></body>\n'
                '</html>')
        return data % {'title': title}


    def to_str(self, encoding='UTF-8'):
        data = [self.header_to_str(encoding),
                stream_to_str_as_xhtml(self.events, encoding)]
        return ''.join(data)


    ########################################################################
    # API
    ########################################################################
    def get_head(self):
        """
        Returns the head element.
        """
        root = self.get_root_element()
        heads = root.get_elements(name='head')
        if heads:
            return heads[0]
        return None


    def get_body(self):
        """
        Returns the body element.
        """
        root = self.get_root_element()
        bodies = root.get_elements(name='body')
        if bodies:
            return bodies[0]
        return None


    ########################################################################
    # API / i18n
    ########################################################################
    def translate(self, catalog):
        def process_message(message, keep_spaces):
            # Normalize the message
            normalize(message)
            # Left strip
            if message:
                x = message[0]
                if isinstance(x, unicode) and x.strip() == u'':
                    del message[0]
                    yield x
            # Right strip
            if message:
                x = message[-1]
                if isinstance(x, unicode) and x.strip() == u'':
                    del message[-1]
                    yield x
            # Process
            if message:
                # XXX
                if len(message) == 1 and isinstance(message[0], Element):
                    node = message[0]
                    open_tag(node)
                    message = Message(node.children)
                    for x in process_message(message, keep_spaces):
                        yield x
                    yield node.get_end_tag()
                else:
                    # Check wether the node message has real text to process.
                    for x in message:
                        if isinstance(x, unicode):
                            if x.strip():
                                break
                        elif isinstance(x, Element):
                            for event, node in x.traverse():
                                if event == TEXT:
                                    if node.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        for event, value in message:
                            if event == TEXT:
                                yield XMLDataType.encode(value)
                            elif event == START_ELEMENT:
                                tag_uri, tag_name, attributes = value
                                open_tag(tag_uri, tag_name, attributes, buffer,
                                         catalog)
                                #msg = Message(x.children)
                                #for y in process_message(msg, keep_spaces):
                                #    yield y
                            elif event == END_ELEMENT:
                                tag_uri, tag_name = value
                                yield get_end_tag(tag_uri, tag_name)
                            elif event == COMMENT:
                                yield '<!--%s-->' % value
                            else:
                                raise NotImplementedError
                        raise StopIteration
                    # Something to translate: segmentation
                    for segment in message.get_segments(keep_spaces):
                        msgstr = catalog.get_translation(segment)
                        # Escapes "&", except when it is an entity reference
                        def f(match):
                            x = match.group(0)
                            if x.endswith(';'):
                                return x
                            return "&amp;" + x[1:]
                        msgstr = re.sub("&[\w;]*", f, msgstr)
                        # XXX The special characters "<" and "&" must be
                        # escaped in text nodes (only in text nodes).

                        yield msgstr
                        if keep_spaces is False:
                            yield u' '

        buffer = StringIO()
        buffer.write(self.header_to_str())
        message = Message()
        keep_spaces = False
        stream = self.traverse()
        for event, value in stream:
            if event == TEXT:
                message.append((event, value))
            elif event == START_ELEMENT:
                # Inline or block
                ns_uri, name, attributes = value
                schema = get_element_schema(ns_uri, name)
                if schema['is_inline']:
                    message.append((event, value))
                    stream.send(1)
                else:
                    # Process any previous message
                    for x in process_message(message, keep_spaces):
                        buffer.write(x.encode('utf-8'))
                    message = Message()
                    # The open tag
                    open_tag(ns_uri, name, attributes, buffer, catalog)
                    # Presarve spaces if <pre>
                    if name == 'pre':
                        keep_spaces = True
            elif event == END_ELEMENT:
                ns_uri, name = value
                schema = get_element_schema(ns_uri, name)
                if not schema['is_inline']:
                    for x in process_message(message, keep_spaces):
                        buffer.write(x.encode('utf-8'))
                    message = Message()
                    # The close tag
                    buffer.write(get_end_tag(ns_uri, name))
                    # </pre> don't preserve spaces any more
                    if name == 'pre':
                        keep_spaces = False
            elif event == COMMENT:
                buffer.write('<!--%s-->' % value.encode('utf-8'))
            else:
                raise NotImplementedError

        # Process trailing message
        if message:
            for x in process_message(message, keep_spaces):
                buffer.write(x.encode('utf-8'))

        data = buffer.getvalue()
        buffer.close()
        return data


    def get_messages(self):
        def process_message(message, keep_spaces):
            # Normalize the message
            normalize(message)
            # Left strip
            if message:
                x = message[0]
                if isinstance(x, unicode) and x.strip() == u'':
                    del message[0]
            # Right strip
            if message:
                x = message[-1]
                if isinstance(x, unicode) and x.strip() == u'':
                    del message[-1]
            # Process
            if message:
                # Check wether the message is only one element
                if len(message) == 1 and isinstance(message[0], Element):
                    node = message[0]
                    message = Message(node.children)
                    for x in process_message(message, keep_spaces):
                        yield x
                else:
                    # Check wether the node message has real text to process.
                    for x in message:
                        if isinstance(x, unicode):
                            if x.strip():
                                break
                        elif isinstance(x, Element):
                            for event, node in x.traverse():
                                if event == TEXT:
                                    if node.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        raise StopIteration
                    # Something to translate: segmentation
                    for segment in message.get_segments(keep_spaces):
                        yield segment

        messages = []
        message = Message()
        keep_spaces = False
        stream = self.traverse()
        for event, node in stram:
            if event == TEXT:
                message.append(node)
            elif event == START_ELEMENT:
                if node.name in ['script', 'style']:
                    for x in process_message(message, keep_spaces):
                        if x not in messages:
                            yield x, 0
                    message = Message()
                    # Don't go through this node
                    stream.send(1)
                else:
                    # Attributes
                    for ns_uri, name, value in node.get_attributes():
                        namespace = get_namespace(ns_uri)
                        if namespace.is_translatable(node, name):
                            if value.strip():
                                if value not in messages:
                                    yield value, 0
                    # Inline or Block
                    schema = get_element_schema(node.namespace, node.name)
                    if schema['is_inline']:
                        message.append(node)
                        stream.send(1)
                    else:
                        for x in process_message(message, keep_spaces):
                            if x not in messages:
                                yield x, 0
                        message = Message()
                        # Presarve spaces if <pre>
                        if node.name == 'pre':
                            keep_spaces = True
            elif event == END_ELEMENT:
                schema = get_element_schema(node.namespace, node.name)
                if not schema['is_inline']:
                    for x in process_message(message, keep_spaces):
                        if x not in messages:
                            yield x, 0
                    message = Message()
                    # </pre> don't preserve spaces any more
                    if node.name == 'pre':
                        keep_spaces = False


XMLDocument.set_doctype_handler('-//W3C//DTD XHTML 1.0 Strict//EN', Document)
register_handler_class(Document)


