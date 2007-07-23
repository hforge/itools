# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import htmlentitydefs
from HTMLParser import HTMLParser
import warnings

# Import from itools
from itools.xml import (XMLError, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT,
    COMMENT, TEXT)
from itools.xhtml import xhtml_uri


# TODO Test the parser with different encodings. The behavior must be
# compatible with the XML parser.

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


class _Parser(HTMLParser, object):

    def parse(self, data):
        self.encoding = 'UTF-8'

        self.events = []
        self.stack = []
        self.feed(data)
        self.close()
        return self.events


    def handle_decl(self, value):
        # The document type declaration of HTML documents is like defined
        # by SGML, what is a little more flexible than XML. Right now we
        # support:
        #
        #   <!DOCTYPE name SYSTEM "system id">
        #   <!DOCTYPE name PUBLIC "public id" "system id">
        #   <!DOCTYPE name PUBLIC "public id">  (*)
        #
        # (*) This case is not allowed by XML.
        #
        # TODO Check online resources to find out other cases that should
        # be supported (the SGML spec is not available online).

        # DOCTYPE
        if not value.startswith('DOCTYPE'):
            raise XMLError
        value = value[7:]
        # Name
        name, value = value.split(None, 1)
        # Ids
        def read_id(value):
            sep = value[0]
            if sep != '"' and sep != "'":
                raise XMLError
            return value[1:].split(sep, 1)

        public_id = None
        system_id = None
        if value.startswith('SYSTEM'):
            value = value[6:].lstrip()
            system_id, value = read_id(value)
        elif value.startswith('PUBLIC'):
            value = value[6:].lstrip()
            public_id, value = read_id(value)
            value = value.lstrip()
            if value:
                system_id, value = read_id(value)
        else:
            raise XMLError
        # Internal subset (FIXME TODO)
        has_internal_subset = None

        value = (name, system_id, public_id, has_internal_subset)
        self.events.append((DOCUMENT_TYPE, value, self.getpos()[0]))


    def handle_starttag(self, name, attrs):
        line = self.getpos()[0]

        # Close missing optional end tags
        if self.stack and self.stack[-1] in close_before_block:
            if name in block_elements:
                tag_name = self.stack.pop()
                self.events.append((END_ELEMENT, (xhtml_uri, tag_name), line))

        # Check the encoding
        if name == 'meta':
            is_content_type = False
            for attribute_name, attribute_value in attrs:
                if attribute_name == 'http-equiv':
                    if attribute_value.lower() == 'content-type':
                        is_content_type = True
                elif attribute_name == 'content':
                    content_value = attribute_value
            if is_content_type is True:
                self.encoding = content_value.split(';')[-1].strip()[8:]

        # Attributes
        attributes = {}
        for attribute_name, attribute_value in attrs:
            if attribute_value is None:
                if attribute_name in boolean_attributes:
                    attribute_value = attribute_name
                else:
                    raise ValueError, \
                          'missing attribute value for "%s"' % attribute_name
            attributes[(xhtml_uri, attribute_name)] = attribute_value

        # Start element
        self.events.append((START_ELEMENT, (xhtml_uri, name, attributes), line))

        # End element
        if name in empty_elements:
            self.events.append((END_ELEMENT, (xhtml_uri, name), line))
        else:
            self.stack.append(name)


    def handle_endtag(self, name):
        line = self.getpos()[0]

        # Discard lonely end tags
        index = len(self.stack) - 1
        while index >= 0 and self.stack[index] != name:
            index = index - 1

        if index < 0:
            # XXX Better to log it
##            warnings.warn('discarding unexpected "</%s>" at line %s'
##                          % (name, line))
            return

        tag_name = self.stack.pop()
        # Close missing optional end tags
        while name != tag_name:
            if tag_name in optional_end_tag_elements:
                tag_name = self.stack.pop()
                self.events.append((END_ELEMENT, (xhtml_uri, tag_name), line))
            else:
                raise ValueError, 'missing end tag </%s>' % tag_name

        self.events.append((END_ELEMENT, (xhtml_uri, name), line))


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



def Parser(data):
    parser = _Parser()
    return parser.parse(data)
