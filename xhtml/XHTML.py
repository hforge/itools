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


# Import from Python
from copy import copy
import re
from sets import Set
from StringIO import StringIO

# Import from itools
from itools.handlers import IO
from itools.xml import XML
from itools import i18n


xhtml_uri = 'http://www.w3.org/1999/xhtml'


#############################################################################
# Namespace
#############################################################################
inline_elements = Set(['a', 'abbr', 'acronym', 'b', 'cite', 'code', 'dfn',
                       'em','kbd', 'q', 'samp', 'span', 'strong', 'sub',
                       'sup', 'tt', 'var'])


class Element(XML.Element):

    namespace = xhtml_uri


    def is_inline(self):
        return self.name in inline_elements


    def is_block(self):
        return self.name not in inline_elements


    def is_translatable(self, attribute_name):
        # Attributes
        if self.name == 'img' and attribute_name == 'alt':
            return True
        if self.name == 'input' and attribute_name == 'value':
            if self.has_attribute(xhtml_uri, 'type'):
                return self.get_attribute(xhtml_uri, 'type') == 'submit'
        return False


class HeadElement(Element):

    def to_unicode(self, encoding='UTF-8'):
        return ''.join([self.get_opentag(),
                        '\n    <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=%s" />' % encoding,
                        XML.Children.encode(self.children, encoding=encoding),
                        self.get_closetag()])


    def set_element(self, element):
        # Skip content type declaration
        if element.namespace == xhtml_uri and element.name == 'meta':
            if element.has_attribute(xhtml_uri, 'http-equiv'):
                value = element.has_attribute(xhtml_uri, 'http-equiv')
                if value == 'Content-Type':
                    return
        self.children.append(element)



class Namespace(XML.Namespace):

    def get_element(cls, prefix, name):
        element_types = {'head': HeadElement}
        element_type = element_types.get(name, Element)
        return element_type(prefix, name)

    get_element = classmethod(get_element)


    def get_attribute_type(local_name):
        attributes = {'src': IO.URI, 'href': IO.URI}
        return attributes.get(local_name, IO.Unicode)

    get_attribute_type = staticmethod(get_attribute_type)



XML.set_namespace(xhtml_uri, Namespace)



#############################################################################
# Document
#############################################################################
class Document(XML.Document):
    """
    This class adds one thing to the XML class, the semantics of translatable
    text.
    """

    class_mimetypes = ['application/xhtml+xml']

    namespace = xhtml_uri

    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self):
        return '<?xml version="1.0" encoding="UTF-8"?>\n' \
               '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n' \
               '       "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n' \
               '<html xmlns="http://www.w3.org/1999/xhtml">\n' \
               '  <head>\n' \
               '    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n' \
               '    <title></title>\n' \
               '  </head>\n' \
               '  <body></body>\n' \
               '</html>'

    ########################################################################
    # i18n API
    ########################################################################
    def translate(self, catalog):
        def open_tag(node):
            # The open tag
            buffer.write(u'<%s' % node.qname)
            # The attributes
            for namespace, local_name, value in node.get_attributes():
                if node.is_translatable(local_name):
                    value = value.strip()
                    if value:
                        value = catalog.get_msgstr(value) or value
                qname = node.get_attribute_qname(namespace, local_name)
                buffer.write(u' %s="%s"' % (qname, unicode(value)))
            buffer.write(u'>')

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
                    yield node.get_closetag()
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
                                yield x.to_unicode()
                        raise StopIteration
                    # Something to translate: segmentation
                    for segment in message.get_segments(keep_spaces):
                        msgstr = catalog.get_msgstr(segment) or segment
                        # Escapes "&", except when it is an entity reference
                        def f(match):
                            x = match.group(0)
                            if x.endswith(';'):
                                return x
                            return "&amp;" + x[1:]
                        msgstr = re.sub("&[\w;]*", f, msgstr)

                        yield msgstr
                        if keep_spaces is False:
                            yield ' '

        buffer = StringIO()
        message = i18n.segment.Message()
        keep_spaces = False
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
                            buffer.write(x)
                        message = i18n.segment.Message()
                        # The open tag
                        open_tag(node)
                        # Presarve spaces if <pre>
                        if node.name == 'pre':
                            keep_spaces = True
                else:
                    if node.is_block():
                        for x in process_message(message, keep_spaces):
                            buffer.write(x)
                        message = i18n.segment.Message()
                        # The close tag
                        buffer.write(node.get_closetag())
                        # </pre> don't preserve spaces any more
                        if node.name == 'pre':
                            keep_spaces = False
            else:
                buffer.write(node.to_unicode())

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
                                    if data.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        raise StopIteration
                    # Something to translate: segmentation
                    for segment in message.get_segments(keep_spaces):
                        segment = segment.replace('"', '\\"')
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
                                yield x
                        message = i18n.segment.Message()
                        # Don't go through this node
                        context.skip = True
                    else:
                        # Attributes
                        for namespace, name, value in node.get_attributes():
                            if node.is_translatable(name):
                                if value.strip():
                                    if value not in messages:
                                        yield value
                        # Inline or Block
                        if node.is_inline():
                            message.append(node)
                            context.skip = True
                        else:
                            for x in process_message(message, keep_spaces):
                                if x not in messages:
                                    yield x
                            message = i18n.segment.Message()
                            # Presarve spaces if <pre>
                            if node.name == 'pre':
                                context.keep_spaces = True
                else:
                    if node.is_block():
                        for x in process_message(message, keep_spaces):
                            if x not in messages:
                                yield x
                        # </pre> don't preserve spaces any more
                        if node.name == 'pre':
                            keep_spaces = False


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


    def to_text(self):
        """
        Removes the markup and returns a plain text string.
        """
        text = ''
        for node in self.traverse():
            if isinstance(node, unicode):
                text += node
        return text



XML.Document.set_doctype_handler('-//W3C//DTD XHTML 1.0 Strict//EN', Document)
XML.Document.register_handler_class(Document)
