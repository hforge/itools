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
import re
from sets import Set
from StringIO import StringIO
from urlparse import urlsplit

# Import from itools
import XML
from itools import i18n
from itools.handlers import IO



#############################################################################
# Namespace
#############################################################################
inline_elements = Set(['a', 'abbr', 'acronym', 'b', 'cite', 'code', 'dfn',
                       'em','kbd', 'q', 'samp', 'span', 'strong', 'sub',
                       'sup', 'tt', 'var'])


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
            if self.has_attribute('type'):
                return self.get_attribute('type') == 'submit'
        return False


    # XXX This is a hack to get the encoding information within the document's
    # head right: the meta element. It only works if the document already
    # contains the meta element.
    # Probably the best solution would be to load the head into a higher
    # level data structure, not as a DOM tree. Though this would break the
    # the XML API.
    def get_opentag(self, encoding='UTF-8'):
        if self.name == 'meta':
            if self.has_attribute('http-equiv'):
                http_equiv = self.get_attribute('http-equiv')
                if http_equiv == 'Content-Type':
                    s = '<%s' % self.qname
                    # Output the attributes
                    for qname, value in self.attributes_by_qname.items():
                        if qname == 'content':
                            value = u'application/xhtml+xml; charset=%s' \
                                    % encoding
                        else:
                            value = unicode(value)
                        s += ' %s="%s"' % (qname, value)
                    # Close the open tag
                    return s + u'>'

        return XML.Element.get_opentag(self, encoding)



class NamespaceHandler(XML.NamespaceHandler):

    def get_element(cls, prefix, name):
        return Element(prefix, name)

    get_element = classmethod(get_element)


    def get_attribute(cls, prefix, name, value):
        if name in ['src', 'href']:
            return IO.URI.decode(value)
        return IO.Unicode.decode(value)

    get_attribute = classmethod(get_attribute)



XML.Document.set_namespace_handler('http://www.w3.org/1999/xhtml',
                                   NamespaceHandler)



#############################################################################
# Document
#############################################################################
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
    def translate(self, catalog):
        def open_tag(node):
            # The open tag
            buffer.write(u'<%s' % node.qname)
            # The attributes
            for qname, value in node.attributes_by_qname.items():
                if node.is_translatable(qname):
                    value = value.strip()
                    if value:
                        value = catalog.get_msgstr(value) or value
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
                    children = [ isinstance(x, XML.Raw) and x.data or x
                                 for x in node.children ]
                    message = i18n.segment.Message(children)
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
                                if isinstance(node, XML.Raw):
                                    if node.data.strip():
                                        break
                            else:
                                continue
                            break
                    else:
                        # Nothing to translate
                        for x in message:
                            yield unicode(x)
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
            if isinstance(node, XML.XMLDeclaration):
                decl = copy(node)
                decl.encoding = 'UTF-8'
                buffer.write(unicode(decl))
            elif isinstance(node, XML.Raw):
                message.append(node.data)
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
                buffer.write(unicode(node))

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
                    children = [ isinstance(x, XML.Raw) and x.data or x
                                 for x in node.children ]
                    message = i18n.segment.Message(children)
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
                                if isinstance(node, XML.Raw):
                                    if node.data.strip():
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
            if isinstance(node, XML.Raw):
                message.append(node.data)
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
            if isinstance(node, XML.Raw):
                text += unicode(node)
        return text



XML.Document.set_doctype_handler('-//W3C//DTD XHTML 1.0 Strict//EN', Document)
XML.Document.register_handler_class(Document)
