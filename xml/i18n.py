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

# Import from the future
from __future__ import absolute_import

# Import from itools
from itools.datatypes import XML as XMLContent
from itools.i18n import Message
from .namespaces import get_namespace, get_element_schema
from .parser import Parser, START_ELEMENT, END_ELEMENT, TEXT, COMMENT



def translate_stack(stack, catalog, keep_spaces):
    """
    This method receives as input a stack of XML events and returns 
    another stack, the translation of the source one.
    """
    from .xml import get_start_tag, get_end_tag

    # Build the message and find out if there is something to translate
    message = Message()
    there_is_something_to_translate = False
    for event, value in stack:
        if event == TEXT:
            if value.strip():
                there_is_something_to_translate = True
            value = XMLContent.encode(value)
            message.append_text(value)
        elif event == START_ELEMENT:
            message.append_format(get_start_tag(*value))
        elif event == END_ELEMENT:
            message.append_format(get_end_tag(*value))
        else:
            raise ValueError
    # If there is nothing to translate, return the same input stack
    if there_is_something_to_translate is False:
        return stack
    # If there is something to translate, translate the message, parse
    # the translation and return the obtained stack
    stack = []
    left = message.lstrip()
    right = message.rstrip()
    if left:
        stack.append((TEXT, left))
    for segment in message.get_segments(keep_spaces):
        segment = catalog.get_translation(segment).encode('utf-8')
        for event, value, line in Parser(segment):
            if event == TEXT:
                value = unicode(value, 'utf-8')
            stack.append((event, value))
    if right:
        stack.append((TEXT, right))
    return stack



def filter_tags(events, tags):
    skip = 0
    for event, value, line in events:
        if skip:
            if event == START_ELEMENT:
                skip += 1
            elif event == END_ELEMENT:
                skip -= 1
            continue

        if event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            if tag_name in tags:
                skip = 1
                continue

        yield event, value



def get_translatable_blocks(events):
    from .xml import get_start_tag, get_end_tag

    message = Message()
    keep_spaces = False

    for event, value in filter_tags(events, ['script', 'style']):
        if event == TEXT:
            message.append_text(value)
        elif event == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Attributes
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                is_translatable = get_namespace(attr_uri).is_translatable
                if is_translatable(tag_uri, tag_name, attributes, attr_name):
                    if value.strip():
                        aux = Message()
                        aux.append_text(value)
                        yield aux, True
            # Inline or Block
            schema = get_element_schema(tag_uri, tag_name)
            if schema.get('is_inline', False):
                value = get_start_tag(tag_uri, tag_name, attributes)
                message.append_format(value)
            else:
                yield message, keep_spaces
                message = Message()
                # Presarve spaces if <pre>
                if tag_name == 'pre':
                    keep_spaces = True
        elif event == END_ELEMENT:
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.get('is_inline', False):
                value = get_end_tag(tag_uri, tag_name)
                message.append_format(value)
            else:
                yield message, keep_spaces
                message = Message()
                # </pre> don't preserve spaces any more
                if tag_name == 'pre':
                    keep_spaces = False



def get_messages(events):
    for message, keep_spaces in get_translatable_blocks(events):
        message.lstrip()
        message.rstrip()
        # If no message, do nothing
        if message.has_text_to_translate() is False:
            continue

        # Check wether the message is only one element
        # FIXME This does not really work
#        if message[0][0] == START_ELEMENT:
#            if message[-1][0] == END_ELEMENT:
#                start_uri, start_name, attributes = message[0]
#                end_uri, end_name = message[-1]
#                if start_uri == end_uri and start_name == end_name:
#                    message = message[0:-1]
#                    for x in process_message(message, keep_spaces):
#                        yield x
#                    continue
        # Something to translate: segmentation
        for segment in message.get_segments(keep_spaces):
            yield segment, 0



class Translatable(object):
    """
    This mixin class provides the user interface that allows to extract
    translatable messages from an XML file, and to build a translated
    file from the origin file and a message catalog.

    The only condition for this to work is that the XML file makes the
    difference between block and inline elements (for example, XHTML).
    """

    def get_messages(self):
        return get_messages(self.events)


    #######################################################################
    # Translate
    #######################################################################
    def _translate(self, catalog):
        namespaces = {}

        stack = []
        keep_spaces = False
        for event, value, line in self.events:
            if event == TEXT:
                stack.append((event, value))
            elif event == START_ELEMENT:
                # Inline or block
                tag_uri, tag_name, attributes = value
                schema = get_element_schema(tag_uri, tag_name)
                if schema['is_inline']:
                    stack.append((event, value))
                else:
                    for x in translate_stack(stack, catalog, keep_spaces):
                        yield x
                    stack = []
                    # The start tag (translate the attributes)
                    aux = {}
                    for attr_uri, attr_name in attributes:
                        value = attributes[(attr_uri, attr_name)]
                        is_trans = get_namespace(attr_uri).is_translatable
                        if is_trans(tag_uri, tag_name, attributes, attr_name):
                            value = value.strip()
                            if value:
                                value = catalog.get_translation(value)
                        aux[(attr_uri, attr_name)] = value
                    yield START_ELEMENT, (tag_uri, tag_name, aux)
                    # Presarve spaces if <pre>
                    if tag_name == 'pre':
                        keep_spaces = True
            elif event == END_ELEMENT:
                tag_uri, tag_name = value
                schema = get_element_schema(tag_uri, tag_name)
                if schema['is_inline']:
                    stack.append((event, value))
                else:
                    for x in translate_stack(stack, catalog, keep_spaces):
                        yield x
                    stack = []
                    # The close tag
                    yield event, value
                    # </pre> don't preserve spaces any more
                    if tag_name == 'pre':
                        keep_spaces = False
            else:
                yield event, value

        # Process trailing message
        if stack:
            for x in translate_stack(stack, catalog, keep_spaces):
                yield x


    def translate(self, catalog):
        from .xml import stream_to_str

        stream = self._translate(catalog)
        return stream_to_str(stream)
