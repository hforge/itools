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

# Import from the Standard Library
from copy import copy
import re
from cStringIO import StringIO

# Import from itools
from itools.datatypes import Integer, Unicode, String, URI
from itools import schemas
from itools.schemas import get_datatype_by_uri
from itools.resources import memory
from itools.xml import XML, namespaces
from itools import i18n


#############################################################################
# Types
#############################################################################

class Element(XML.Element):

    namespace = 'http://www.w3.org/1999/xhtml'


    def is_inline(self):
        raise NotImplementedError


    def is_block(self):
        raise NotImplementedError


    def get_start_tag_as_html(self):
        s = '<%s' % self.qname
        # Output the attributes
        for namespace_uri, local_name, value in self.get_attributes():
            qname = self.get_attribute_qname(namespace_uri, local_name)
            type = schemas.get_datatype_by_uri(namespace_uri, local_name)
            value = type.encode(value)
            s += ' %s="%s"' % (qname, value)
        return s + '>'


    def get_content_as_html(self, encoding='UTF-8'):
        s = []
        for node in self.children:
            if isinstance(node, unicode):
                # XXX This is equivalent to 'Unicode.encode',
                # there should be a single place.
                s.append(node.replace('&', '&amp;').replace('<', '&lt;'))
            elif isinstance(node, Element):
                s.append(node.get_start_tag_as_html())
                s.append(node.get_content_as_html())
                s.append(node.get_end_tag())
            else:
                s.append(node.to_str(encoding=encoding))
        return ''.join(s)


    def is_translatable(self, attribute_name):
        # Attributes
        if self.name == 'img' and attribute_name == 'alt':
            return True
        if self.name == 'input' and attribute_name == 'value':
            if self.has_attribute(Namespace.class_uri, 'type'):
                return self.get_attribute(Namespace.class_uri, 'type') == 'submit'
        return False



class InlineElement(Element):

    def is_inline(self):
        return True


    def is_block(self):
        return False



class BlockElement(Element):

    def is_inline(self):
        return False


    def is_block(self):
        return True



class HeadElement(BlockElement):

    def to_str(self, encoding='UTF-8'):
        head = []
        head.append('<head>\n')

        # The content type
        head.append('    <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=%s" />\n' % encoding)

        # The rest of the head
        content = self.get_content(encoding)
        lines = content.splitlines()
        while lines and lines[0].strip() == u'':
            lines = lines[1:]
        head.append('\n'.join(lines))

        head.append('</head>')
        return ''.join(head)


    def set_element(self, element):
        # Skip content type declaration
        xhtml_namespace = Namespace.class_uri
        if element.namespace == xhtml_namespace and element.name == 'meta':
            if element.has_attribute(xhtml_namespace, 'http-equiv'):
                value = element.get_attribute(xhtml_namespace, 'http-equiv')
                if value == 'Content-Type':
                    return
        self.children.append(element)


#############################################################################
# Namespace
#############################################################################

elements_schema = {
    # XHTML 1.0 strict
    'area': {'type': BlockElement, 'is_empty': True},
    'base': {'type': BlockElement, 'is_empty': True},
    'br': {'type': BlockElement, 'is_empty': True},
    'col': {'type': BlockElement, 'is_empty': True},
    'hr': {'type': BlockElement, 'is_empty': True},
    'img': {'type': BlockElement, 'is_empty': True},
    'input': {'type': BlockElement, 'is_empty': True},
    'link': {'type': BlockElement, 'is_empty': True},
    'meta': {'type': BlockElement, 'is_empty': True},
    'param': {'type': BlockElement, 'is_empty': True},
    # XHTML 1.0 transitional
    'basefont': {'type': BlockElement, 'is_empty': True},
    'isindex': {'type': BlockElement, 'is_empty': True},
    # XHTML 1.0 frameset
    'frame': {'type': BlockElement, 'is_empty': True},
    # Vendor specific, not approved by W3C
    'embed': {'type': BlockElement, 'is_empty': True},
    # Unclassified
    'a': {'type': InlineElement, 'is_empty': False},
    'abbr': {'type': InlineElement, 'is_empty': False},
    'acronym': {'type': InlineElement, 'is_empty': False},
    'b': {'type': InlineElement, 'is_empty': False},
    'cite': {'type': InlineElement, 'is_empty': False},
    'code': {'type': InlineElement, 'is_empty': False},
    'dfn': {'type': InlineElement, 'is_empty': False},
    'em': {'type': InlineElement, 'is_empty': False},
    'head': {'type': HeadElement, 'is_empty': False},
    'kbd': {'type': InlineElement, 'is_empty': False},
    'q': {'type': InlineElement, 'is_empty': False},
    'samp': {'type': InlineElement, 'is_empty': False},
    'span': {'type': InlineElement, 'is_empty': False},
    'strong': {'type': InlineElement, 'is_empty': False},
    'sub': {'type': InlineElement, 'is_empty': False},
    'sup': {'type': InlineElement, 'is_empty': False},
    'tt': {'type': InlineElement, 'is_empty': False},
    'var': {'type': InlineElement, 'is_empty': False},
    }


class Namespace(namespaces.AbstractNamespace):

    class_uri = 'http://www.w3.org/1999/xhtml'
    class_prefix = None


    @staticmethod
    def get_element_schema(name):
        default_schema = {'type': BlockElement,
                          'is_empty': False}
        return elements_schema.get(name, default_schema)

namespaces.set_namespace(Namespace)



class Schema(schemas.base.Schema):

    class_uri = 'http://www.w3.org/1999/xhtml'
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

                 'href': URI,
                 'src': URI,
                 'title': Unicode,
                 }


    @classmethod
    def get_datatype(cls, name):
        return cls.datatypes.get(name, Unicode)

schemas.register_schema(Schema)



#############################################################################
# Document
#############################################################################
class Document(XML.Document):
    """
    This class adds one thing to the XML class, the semantics of translatable
    text.
    """

    class_mimetypes = ['application/xhtml+xml']
    class_extension = 'xhtml'

    namespace = 'http://www.w3.org/1999/xhtml'

    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self, title=''):
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


    ########################################################################
    # API
    ########################################################################
    def get_head(self):
        """
        Returns the head element.
        """
        root = self.get_root_element()
        heads = [ x for x in root.get_elements() if x.name == 'head' ]
        if heads:
            return heads[0]
        return None


    def get_body(self):
        """
        Returns the body element.
        """
        root = self.get_root_element()
        bodies = [ x for x in root.get_elements() if x.name == 'body' ]
        if bodies:
            return bodies[0]
        return None


    ########################################################################
    # API / i18n
    ########################################################################
    def translate(self, catalog):
        def open_tag(node):
            # The open tag
            buffer.write('<%s' % node.qname)
            # The attributes
            for namespace, local_name, value in node.get_attributes():
                if node.is_translatable(local_name):
                    value = value.strip()
                    if value:
                        value = catalog.get_translation(value)
                        #value = catalog.get_msgstr(value) or value
                qname = node.get_attribute_qname(namespace, local_name)
                datatype = schemas.get_datatype_by_uri(namespace, local_name)
                buffer.write(' %s="%s"' % (qname, datatype.encode(value)))
            # Close the start tag
            namespace = namespaces.get_namespace(node.namespace)
            schema = namespace.get_element_schema(node.name)
            is_empty = schema.get('is_empty', False)
            if is_empty:
                buffer.write('/>')
            else:
                buffer.write('>')

        def process_message(message, keep_spaces):
            # Normalize the message
            message.normalize()
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
                if len(message) == 1 and isinstance(message[0], XML.Element):
                    node = message[0]
                    open_tag(node)
                    message = i18n.segment.Message(node.children)
                    for x in process_message(message, keep_spaces):
                        yield x
                    yield node.get_end_tag()
                else:
                    # Check wether the node message has real text to process.
                    for x in message:
                        if isinstance(x, unicode):
                            if x.strip():
                                break
                        elif isinstance(x, XML.Element):
                            for node in x.traverse():
                                if isinstance(node, unicode):
                                    if node.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        for x in message:
                            if isinstance(x, unicode):
                                yield x
                            else:
                                yield x.to_str()
                        raise StopIteration
                    # Something to translate: segmentation
                    for segment in message.get_segments(keep_spaces):
                        msgstr = catalog.get_translation(segment)
                        #msgstr = catalog.get_msgstr(segment) or segment
                        # Escapes "&", except when it is an entity reference
                        def f(match):
                            x = match.group(0)
                            if x.endswith(';'):
                                return x
                            return "&amp;" + x[1:]
                        msgstr = re.sub("&[\w;]*", f, msgstr)

                        yield msgstr
                        if keep_spaces is False:
                            yield u' '

        buffer = StringIO()
        buffer.write(self.header_to_str())
        message = i18n.segment.Message()
        keep_spaces = False
        root_element = self.get_root_element()
        for node, context in self.traverse2():
            if isinstance(node, unicode):
                message.append(node)
            elif isinstance(node, XML.Element):
                if context.start:
                    # Inline or block
                    if node.is_inline():
                        message.append(node)
                        context.skip = True
                    else:
                        # Process any previous message
                        for x in process_message(message, keep_spaces):
                            buffer.write(x.encode('utf-8'))
                        message = i18n.segment.Message()
                        # The open tag
                        open_tag(node)
                        # Presarve spaces if <pre>
                        if node.name == 'pre':
                            keep_spaces = True
                else:
                    if node.is_block():
                        for x in process_message(message, keep_spaces):
                            buffer.write(x.encode('utf-8'))
                        message = i18n.segment.Message()
                        # The close tag
                        buffer.write(node.get_end_tag())
                        # </pre> don't preserve spaces any more
                        if node.name == 'pre':
                            keep_spaces = False
            else:
                buffer.write(node.to_str())

        data = buffer.getvalue()
        buffer.close()
        return data


    def get_messages(self):
        def process_message(message, keep_spaces):
            # Normalize the message
            message.normalize()
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
                if len(message) == 1 and isinstance(message[0], XML.Element):
                    node = message[0]
                    message = i18n.segment.Message(node.children)
                    for x in process_message(message, keep_spaces):
                        yield x
                else:
                    # Check wether the node message has real text to process.
                    for x in message:
                        if isinstance(x, unicode):
                            if x.strip():
                                break
                        elif isinstance(x, XML.Element):
                            for node in x.traverse():
                                if isinstance(node, unicode):
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
        message = i18n.segment.Message()
        keep_spaces = False
        for node, context in self.traverse2():
            if isinstance(node, unicode):
                message.append(node)
            elif isinstance(node, XML.Element):
                if context.start:
                    if node.name in ['script', 'style']:
                        for x in process_message(message, keep_spaces):
                            if x not in messages:
                                yield x, 0
                        message = i18n.segment.Message()
                        # Don't go through this node
                        context.skip = True
                    else:
                        # Attributes
                        for namespace, name, value in node.get_attributes():
                            if node.is_translatable(name):
                                if value.strip():
                                    if value not in messages:
                                        yield value, 0
                        # Inline or Block
                        if node.is_inline():
                            message.append(node)
                            context.skip = True
                        else:
                            for x in process_message(message, keep_spaces):
                                if x not in messages:
                                    yield x, 0
                            message = i18n.segment.Message()
                            # Presarve spaces if <pre>
                            if node.name == 'pre':
                                context.keep_spaces = True
                else:
                    if node.is_block():
                        for x in process_message(message, keep_spaces):
                            if x not in messages:
                                yield x, 0
                        # </pre> don't preserve spaces any more
                        if node.name == 'pre':
                            keep_spaces = False


XML.Document.set_doctype_handler('-//W3C//DTD XHTML 1.0 Strict//EN', Document)
XML.Document.register_handler_class(Document)



########################################################################
# API / Change relative links
########################################################################
def resolve_pointer(uri, offset):
    if uri.path.is_relative():
        # XXX Here we loss the query and fragment.
        return offset.resolve(uri.path)

    return uri
##    uri = str(uri)[1:]
##    return here.get_pathtoroot() + uri


def set_template_prefix(handler, offset, encoding='UTF-8'):
    # Set the prefix
    data = []
    data.append(handler.header_to_str())
    # Let's go!
    for node, context in handler.traverse2():
        if isinstance(node, XML.Element):
            if context.start:
                data.append('<%s' % node.qname)
                for namespace, local_name, value in node.get_attributes():
                    qname = node.get_attribute_qname(namespace, local_name)
                    encoded = False
                    if local_name in ('href', 'src'):
                        if not value.scheme and not value.authority:
                            value = resolve_pointer(value, offset)
                            encoded = True
                    elif node.qname == 'param' and local_name == 'value':
                        name = node.get_attribute(namespace, 'name')
                        # Special case for Flash objects
                        # but others possible (Java, etc.)
                        if name == 'movie':
                            uri = URI.decode(value)
                            if not uri.scheme and not uri.authority:
                                value = resolve_pointer(uri, offset)
                                encoded = True
                    if not encoded:
                        datatype = get_datatype_by_uri(namespace, local_name)
                        value = datatype.encode(value)
                    data.append(' %s="%s"' % (qname, value))
                data.append('>')
            else:
                data.append('</%s>' % node.qname)
        elif isinstance(node, XML.Comment):
            data.append(node.to_str())
        elif isinstance(node, unicode):
            data.append(node.encode(encoding))
        else:
            raise ValueError, 'unexpected value "%s"' % node

    data = ''.join(data)
    resource = memory.File(data)
    return Document(resource)
