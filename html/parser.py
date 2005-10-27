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
import htmlentitydefs
from HTMLParser import HTMLParser
import warnings


DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, COMMENT, TEXT = range(5)


# List of empty elements, which don't have a close tag
# XXX Sentenced to dead, to use namespace schema instead.
empty_elements = set([
    # XHTML 1.0 strict
    'area', 'base', 'br', 'col', 'hr', 'img', 'input', 'link', 'meta', 'param',
    # XHTML 1.0 transitional
    'basefont', 'isindex',
    # XHTML 1.0 frameset
    'frame',
    # Vendor specific, not approved by W3C
    'embed'])


# Elements whose end tag is optional
optional_end_tag_elements = set(['body', 'colgroup', 'dd', 'dt', 'head',
                                 'html', 'li', 'option', 'p', 'tbody', 'td',
                                 'tfoot', 'th', 'thead', 'tr'])

# Elements whose end tag is optional and which can not contain a block tag
# (hence must be closed before). XXX Finish.
close_before_block = set(['dd', 'dt', 'p'])


# Block elements
block_elements = set([
    'address', 'blockquote', 'center', 'dir', 'div', 'dl', 'fieldset', 'form',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'isindex', 'menu', 'noframes',
    'noscript', 'ol', 'p', 'pre', 'table', 'ul',
    # Considered as block elements because they can contain block elements
    'dd', 'dt', 'frameset', 'li', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr',
    ])

# Boolean attributes
boolean_attributes = set(['checked', 'compact', 'declare', 'defer',
                          'disabled', 'ismap', 'multiple', 'nohref',
                          'noresize', 'noshade', 'nowrap', 'readonly',
                          'selected'])


class Parser(HTMLParser):

    def parse(self, data):
        self.encoding = 'UTF-8'

        self.events = []
        self.stack = []
        self.feed(data)
        self.close()
        return self.events


    def handle_decl(self, declaration):
        # XXX This is related with the XML doctype, it should have a similar
        # structure.
        self.events.append((DOCUMENT_TYPE, declaration, self.getpos()[0]))


    def handle_starttag(self, name, attrs):
        line_number = self.getpos()[0]

        # Close missing optional end tags
        if self.stack and self.stack[-1] in close_before_block:
            if name in block_elements:
                element_name = self.stack.pop()
                self.events.append((END_ELEMENT, element_name, line_number))

        # Check the encoding
        if name == 'meta':
            if ('http-equiv', 'Content-Type') in attrs:
                for attribute_name, attribute_value in attrs:
                    if attribute_name == 'content':
                        encoding = attribute_value.split(';')[-1].strip()[8:]
                        self.encoding = encoding
                        break

        # Attributes
        attributes = {}
        for attribute_name, attribute_value in attrs:
            if attribute_value is None:
                if attribute_name in boolean_attributes:
                    attribute_value = attribute_name
                else:
                    raise ValueError, \
                          'missing attribute value for "%s"' % attribute_name
            attributes[attribute_name] = attribute_value

        # Start element
        self.events.append((START_ELEMENT, (name, attributes), line_number))

        # End element
        if name in empty_elements:
            self.events.append((END_ELEMENT, name, line_number))
        else:
            self.stack.append(name)


    def handle_endtag(self, name):
        line_number = self.getpos()[0]

        # Discard lonely end tags
        index = len(self.stack) - 1
        while index >= 0 and self.stack[index] != name:
            index = index - 1

        if index < 0:
            # XXX Better to log it
##            warnings.warn('discarding unexpected "</%s>" at line %s'
##                          % (name, line_number))
            return

        element_name = self.stack.pop()
        # Close missing optional end tags
        while name != element_name:
            if element_name in optional_end_tag_elements:
                element_name = self.stack.pop()
                self.events.append((END_ELEMENT, element_name, line_number))
            else:
                raise ValueError, 'missing end tag </%s>' % element_name

        self.events.append((END_ELEMENT, name, line_number))


    def handle_comment(self, data):
        self.events.append((COMMENT, data, self.getpos()[0]))


    def handle_data(self, data):
        self.events.append((TEXT, data, self.getpos()[0]))


    def handle_entityref(self, name):
        # XXX Copied from 'itools.xml.parser.Parser.skipped_entity_handler'
        if name in htmlentitydefs.name2codepoint:
            codepoint = htmlentitydefs.name2codepoint[name]
            char = unichr(codepoint)
            try:
                char = char.encode(self.encoding)
            except UnicodeEncodeError:
                # XXX Error. Entity references allow to use characters that
                # can not be represented on the document encoding. But our
                # policy is to translate these entity references to that
                # encoding, what is a contradiction. Just try to parse
                # a document on latin with the entity "&rsquo;".
                pass
            else:
                self.events.append((TEXT, char, self.getpos()[0]))
        else:
            warnings.warn('Unknown entity reference "%s" (ignoring)' % name)


    # XXX handlers that remain to implement include
##    def handle_pi(self, data):
