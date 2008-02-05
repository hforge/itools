# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from HTMLParser import HTMLParser as BaseParser, HTMLParseError
from warnings import warn

# Import from itools
from itools.xml import (XMLError, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT,
    COMMENT, TEXT)
from xhtml import xhtml_uri


# TODO Test the parser with different encodings. The behavior must be
# compatible with the XML parser.

###########################################################################
# DTD (transitional)
# TODO Implement parsing and support of any DTD
###########################################################################
dtd_TEXT = 0  # PCDATA or CDATA
dtd_empty = frozenset()
dtd_fontstyle = frozenset(['tt', 'i', 'b', 'u', 's', 'strike', 'big', 'small'])
dtd_phrase = frozenset(['em', 'strong', 'dfn', 'code', 'samp', 'kbd', 'var',
    'cite', 'abbr', 'acronym'])
dtd_special = frozenset(['a', 'img', 'applet', 'object', 'font', 'basefont',
    'br', 'script', 'map', 'q', 'sub', 'sup', 'span', 'bdo', 'iframe'])
dtd_formctrl = frozenset(['input', 'select', 'textarea', 'label', 'button'])
dtd_inline = (frozenset([dtd_TEXT]) | dtd_fontstyle | dtd_phrase | dtd_special
    | dtd_formctrl)

dtd_heading = frozenset(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
dtd_list = frozenset(['ul', 'ol', 'dir', 'menu'])
dtd_preformatted = frozenset(['pre'])
dtd_block = dtd_heading | dtd_list | dtd_preformatted | frozenset(['p',
    'dl', 'div', 'center', 'noscript', 'noframes', 'blockquote', 'form',
    'isindex', 'hr', 'table', 'fieldset', 'address'])
dtd_flow = dtd_block | dtd_inline
dtd_ = frozenset([])


# FIXME This code is duplicated from "itools.html.xhtml" (actually, this one
# is more complete).
dtd = {
    # Strict (http://www.w3.org/TR/html4/sgml/dtd.html)
    'a': {'contains': dtd_inline},
    'abbr': {'contains': dtd_inline},
    'acronym': {'contains': dtd_inline},
    'address': {'contains': dtd_inline},
    'area': {'contains': dtd_empty},
    'b': {'contains': dtd_inline},
    'base': {'contains': dtd_empty},
    'bdo': {'contains': dtd_inline},
    'big': {'contains': dtd_inline},
    'blockquote': {'contains': dtd_block},
    'body': {'contains': dtd_flow | frozenset(['del', 'ins'])},
    'br': {'contains': dtd_empty},
    'button': {'contains': dtd_flow - (dtd_formctrl | frozenset(['a', 'form',
                                       'isindex', 'fieldset', 'iframe']))},
    'caption': {'contains': dtd_inline},
    'cite': {'contains': dtd_inline},
    'code': {'contains': dtd_inline},
    'col': {'contains': dtd_empty},
    'colgroup': {'contains': frozenset(['col'])},
    'dd': {'contains': dtd_flow},
    'del': {'contains': dtd_flow},
    'dfn': {'contains': dtd_inline},
    'div': {'contains': dtd_flow},
    'dl': {'contains': frozenset(['dt', 'dd'])},
    'dt': {'contains': dtd_inline},
    'em': {'contains': dtd_inline},
    'fieldset': {'contains': frozenset([dtd_TEXT, 'legend']) | dtd_flow},
    'form': {'contains': dtd_block - frozenset(['form'])},
    'h1': {'contains': dtd_inline},
    'h2': {'contains': dtd_inline},
    'h3': {'contains': dtd_inline},
    'h4': {'contains': dtd_inline},
    'h5': {'contains': dtd_inline},
    'h6': {'contains': dtd_inline},
    'head': {'contains': frozenset(['title', 'isindex', 'base', 'script',
                                    'style', 'meta', 'link', 'object'])},
    'hr': {'contains': dtd_empty},
    'html': {'contains': frozenset(['head', 'body', 'frameset'])},
    'i': {'contains': dtd_inline},
    'img': {'contains': dtd_empty},
    'ins': {'contains': dtd_flow},
    'input': {'contains': dtd_empty},
    'kbd': {'contains': dtd_inline},
    'label': {'contains': dtd_inline - frozenset(['label'])},
    'legend': {'contains': dtd_inline},
    'li': {'contains': dtd_flow},
    'link': {'contains': dtd_empty},
    'map': {'contains': dtd_block | frozenset(['area'])},
    'meta': {'contains': dtd_empty},
    'noscript': {'contains': dtd_block},
    'object': {'contains': frozenset(['param']) | dtd_flow},
    'ol': {'contains': frozenset(['li'])},
    'optgroup': {'contains': frozenset(['option'])},
    'option': {'contains': frozenset([dtd_TEXT])},
    'p': {'contains': dtd_inline},
    'param': {'contains': dtd_empty},
    'pre': {'contains': dtd_inline - frozenset(['img', 'object', 'applet',
                                                'big', 'small', 'sub', 'sup',
                                                'font', 'basefont'])},
    'q': {'contains': dtd_inline},
    'samp': {'contains': dtd_inline},
    'script': {'contains': frozenset([dtd_TEXT])},
    'select': {'contains': frozenset(['optgroup', 'option'])},
    'small': {'contains': dtd_inline},
    'span': {'contains': dtd_inline},
    'strong': {'contains': dtd_inline},
    'style': {'contains': frozenset([dtd_TEXT])},
    'sub': {'contains': dtd_inline},
    'sup': {'contains': dtd_inline},
    'table': {'contains': frozenset(['caption', 'col', 'colgroup', 'thead',
                                     'tfoot', 'tbody'])},
    'tbody': {'contains': frozenset(['tr'])},
    'td': {'contains': dtd_flow},
    'textarea': {'contains': frozenset([dtd_TEXT])},
    'tfoot': {'contains': frozenset(['tr'])},
    'th': {'contains': dtd_flow},
    'thead': {'contains': frozenset(['tr'])},
    'title': {'contains': frozenset([dtd_TEXT])},
    'tr': {'contains': frozenset(['th', 'td'])},
    'tt': {'contains': dtd_inline},
    'ul': {'contains': frozenset(['li'])},
    'var': {'contains': dtd_inline},
    # Loose (http://www.w3.org/TR/html4/sgml/loosedtd.html)
    'applet': {'contains': frozenset(['param']) | dtd_flow},
    'basefont': {'contains': dtd_empty},
    'center': {'contains': dtd_flow},
    'dir': {'contains': frozenset(['li'])},
    'font': {'contains': dtd_inline},
    'iframe': {'contains': dtd_flow},
    'isindex': {'contains': dtd_empty},
    'menu': {'contains': frozenset(['li'])},
    's': {'contains': dtd_inline},
    'strike': {'contains': dtd_inline},
    'u': {'contains': dtd_inline},
    # Frames (XXX)
    'frame': {'contains': dtd_empty},
    'frameset': {'contains': frozenset(['frameset', 'frame', 'noframes'])},
    'noframes': {'contains': dtd_flow},
    # Vendor specific, not approved by W3C
    'embed': {'contains': dtd_empty},
    }



# Elements whose end tag is optional
optional_end_tag_elements = set(['body', 'colgroup', 'dd', 'dt', 'head',
                                 'html', 'li', 'option', 'p', 'tbody', 'td',
                                 'tfoot', 'th', 'thead', 'tr'])

# Boolean attributes
boolean_attributes = set(['checked', 'compact', 'declare', 'defer',
                          'disabled', 'ismap', 'multiple', 'nohref',
                          'noresize', 'noshade', 'nowrap', 'readonly',
                          'selected'])


###########################################################################
# The Parser
###########################################################################
class Parser(BaseParser, object):

    def parse(self, data):
        self.encoding = 'UTF-8'

        self.events = []
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
        events = self.events
        line = self.getpos()[0]

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
                    message = 'missing attribute value for "%s"'
                    raise XMLError, message % attribute_name
            attributes[(xhtml_uri, attribute_name)] = attribute_value

        # Start element
        events.append((START_ELEMENT, (xhtml_uri, name, attributes), line))


    def handle_endtag(self, name):
        self.events.append((END_ELEMENT, (xhtml_uri, name), self.getpos()[0]))


    def handle_comment(self, data):
        self.events.append((COMMENT, data, self.getpos()[0]))


    def handle_data(self, data):
        self.events.append((TEXT, data, self.getpos()[0]))


    def handle_entityref(self, name):
        # FIXME Duplicated code, also written in C in "xml/parser.c".
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
            warn('Unknown entity reference "%s" (ignoring)' % name)


    # TODO handlers that remain to implement include
##    def handle_pi(self, data):



def make_xml_compatible(stream):
    stack = []
    for event in stream:
        type, value, line = event
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Close missing optional end tags
            n = len(stack)
            if n > 0 and stack[-1] in optional_end_tag_elements:
                if tag_name not in dtd[stack[-1]]['contains']:
                    if (n == 1) or (tag_name in dtd[stack[-2]]['contains']):
                        last = stack.pop()
                        yield END_ELEMENT, (tag_uri, last), line
            # Yield
            yield event
            # Close empty tags
            if tag_name in dtd and dtd[tag_name]['contains'] is dtd_empty:
                yield END_ELEMENT, (tag_uri, tag_name), line
            else:
                stack.append(tag_name)
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            # Discard lonely end tags
            index = len(stack) - 1
            while index >= 0 and stack[index] != tag_name:
                index = index - 1

            if index < 0:
                # XXX Warning!?
                continue

            last = stack.pop()
            # Close missing optional end tags
            while tag_name != last:
                if last in optional_end_tag_elements:
                    yield END_ELEMENT, (xhtml_uri, last), line
                    last = stack.pop()
                else:
                    msg = 'missing end tag </%s> at line %s'
                    raise XMLError, msg % (last, line)
            yield event
        else:
            yield event

    # Close missing optional end tags
    while stack:
        last = stack.pop()
        if last in optional_end_tag_elements:
            yield END_ELEMENT, (xhtml_uri, last), line
        else:
            msg = 'missing end tag </%s> at line %s'
            raise XMLError, msg % (last, line)



def HTMLParser(data):
    try:
        stream = Parser().parse(data)
    except HTMLParseError, message:
        raise XMLError, message
    stream = make_xml_compatible(stream)
    # TODO Don't transform to a list, keep the stream
    return list(stream)
