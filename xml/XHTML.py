# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from sets import Set
from StringIO import StringIO
from urlparse import urlsplit

# Import from itools
import XML
from itools import i18n



inline_elements = ['a', 'abbr', 'acronym', 'b', 'cite', 'code', 'dfn', 'em',
                   'kbd', 'q', 'samp', 'span', 'strong', 'sub', 'sup', 'tt',
                   'var']



class Attribute(XML.Attribute):
    """ """



class Element(XML.Element):
    namespace = 'http://www.w3.org/1999/xhtml'


    def is_inline(self):
        return self.name in inline_elements


    def is_block(self):
        return self.name not in inline_elements


    def is_translatable(self, attribute_name):
        # Attributes
        if self.name == 'img' and attribute_name == 'alt':
            return True
        if self.name == 'input' and attribute_name == 'value':
            attribute = self.attributes.get('type')
            if attribute and attribute.value == 'submit':
                return True
        return False



class Document(XML.Document):
    """
    This class adds one thing to the XML class, the semantics of translatable
    text.
    """

    class_mimetypes = ['application/xhtml+xml']

    namespace = 'http://www.w3.org/1999/xhtml'

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
    def translate(self, catalog, node=None):
        """ """
        def open_tag(node, context):
            buffer = context.buffer
            # The open tag
            buffer.write(u'<%s' % node.qname)
            # The attributes
            for attribute in node.attributes:
                if node.is_translatable(attribute.name):
                    msgid = attribute.value.strip()
                    if msgid:
                        msgstr = catalog.get_msgstr(msgid) or msgid
                    else:
                        msgstr = msgid
                    buffer.write(u' %s="%s"' % (attribute.qname, msgstr))
                else:
                    buffer.write(u' %s' % unicode(attribute))
            buffer.write(u'>')

        def process_message(context):
            # Get the message to process and set a new message in the context
            message = context.message
            context.message = i18n.segment.Message()
            # Normalize the message
            message.normalize()
            # Left strip
            if message:
                x = message[0]
                if isinstance(x, unicode) and x.strip() == u'':
                    del message[0]
                    context.buffer.write(x)
            # Right strip
            if message:
                x = message[-1]
                if isinstance(x, unicode) and x.strip() == u'':
                    del message[-1]
                    context.buffer.write(x)
            # Process
            if message:
                # XXX
                if len(message) == 1 and isinstance(message[0], XML.Element):
                    node = message[0]
                    open_tag(node, context)
                    children = [ isinstance(x, XML.Raw) and x.data or x
                                 for x in node.children ]
                    context.message = i18n.segment.Message(children)
                    process_message(context)
                    context.buffer.write(node.get_closetag())
                else:
                    # Check wether the node message has real text to process.
                    for x in message:
                        if isinstance(x, unicode):
                            if x.strip():
                                break
                        elif isinstance(x, XML.Element):
                            for node in x.traverse():
                                if isinstance(node, XML.Raw):
                                    if node.data.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        for x in message:
                            context.buffer.write(unicode(x))
                        return
                    # Something to translate: segmentation
                    for segment in message.get_segments(context.keep_spaces):
                        msgstr = catalog.get_msgstr(segment) or segment
                        msgstr = msgstr.replace('&', '&amp;')
                        context.buffer.write(msgstr)
                        if context.keep_spaces is False:
                            context.buffer.write(' ')

        def before(node, context):
            buffer = context.buffer
            message = context.message
            if isinstance(node, XML.XMLDeclaration):
                decl = copy(node)
                decl.encoding = 'UTF-8'
                buffer.write(unicode(decl))
            elif isinstance(node, XML.Raw):
                message.append(node.data)
            elif isinstance(node, XML.Element):
                # Inline or block
                if node.is_inline():
                    message.append(node)
                    return True
                else:
                    # Process any previous message
                    process_message(context)
                    # The open tag
                    open_tag(node, context)
                    # Presarve spaces if <pre>
                    if node.name == 'pre':
                        context.keep_spaces = True
            else:
                buffer.write(unicode(node))

        def after(node, context):
            if isinstance(node, XML.Element):
                if node.is_block():
                    process_message(context)
                    # The close tag
                    context.buffer.write(node.get_closetag())
                    # </pre> don't preserve spaces any more
                    if node.name == 'pre':
                        context.keep_spaces = False

        context = XML.Context()
        context.catalog = catalog
        context.buffer = StringIO()
        context.message = i18n.segment.Message()
        context.keep_spaces = False
        self.walk(before, after, context)
        data = context.buffer.getvalue()
        context.buffer.close()
        return data


    def get_messages(self):
        def process_message(context):
            # Get the message to process and set a new message in the context
            message = context.message
            context.message = i18n.segment.Message()
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
                    children = [ isinstance(x, XML.Raw) and x.data or x
                                 for x in node.children ]
                    context.message = i18n.segment.Message(children)
                    process_message(context)
                else:
                    # Check wether the node message has real text to process.
                    for x in message:
                        if isinstance(x, unicode):
                            if x.strip():
                                break
                        elif isinstance(x, XML.Element):
                            for node in x.traverse():
                                if isinstance(node, XML.Raw):
                                    if node.data.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        return
                    # Something to translate: segmentation
                    for segment in message.get_segments(context.keep_spaces):
                        segment = segment.replace('"', '\\"')
                        if segment not in context.messages:
                            context.messages.append(segment)

        def before(node, context):
            message = context.message
            if isinstance(node, XML.Raw):
                message.append(node.data)
            elif isinstance(node, XML.Element):
                # Skip <script> and <style>
                if node.name == 'script' or node.name == 'style':
                    process_message(context)
                    return True
                # Attributes
                for attribute in node.attributes:
                    if node.is_translatable(attribute.name):
                        value = attribute.value.strip()
                        if value:
                            if attribute.value not in context.messages:
                                context.messages.append(attribute.value)
                # Inline or Block
                if node.is_inline():
                    message.append(node)
                    return True
                else:
                    process_message(context)
                    # Presarve spaces if <pre>
                    if node.name == 'pre':
                        context.keep_spaces = True

        def after(node, context):
            if isinstance(node, XML.Element):
                if node.is_block():
                    process_message(context)
                    # </pre> don't preserve spaces any more
                    if node.name == 'pre':
                        context.keep_spaces = False

        context = XML.Context()
        context.messages = []
        context.message = i18n.segment.Message()
        context.keep_spaces = False
        self.walk(before, after, context)
        # Process last message
        process_message(context)

        return context.messages


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
            if isinstance(node, XML.Raw):
                text += unicode(node)
        return text




########################################################################
# Interface for the XML parser, factories
class NSHandler(object):
    def get_element(self, prefix, name):
        return Element(prefix, name)


    def get_attribute(self, prefix, name, value):
        return Attribute(prefix, name, value)


########################################################################
# Register
XML.registry.set_namespace('http://www.w3.org/1999/xhtml', NSHandler())
XML.registry.set_doctype('-//W3C//DTD XHTML 1.0 Strict//EN', Document)

XML.Document.register_handler_class(Document)
