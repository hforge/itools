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



TRANSLATABLE_BLOCK = 999

def get_translatable_blocks(events):
    """
    This method is defined so it can be used by both "get_messages" and
    "translate". Hence it contains the logic that is commont to both, to
    avoid code duplication.

    It returns the back the events it receives, except that it finds out
    when a sequence of events defines a translatable block; then this block
    sequence is returned, identified by an special event type
    (TRANSLATABLE_BLOCK).

    A translatable block is one that:
    
      - contains at least one non-empty text node;
      - does not contain block-elements;

    We also do not consider sourronding inline-elements. For example,
    in "<em>Hello baby</em>" the translatable block is just the text
    node "Hello baby". But in "Hello <em>baby</em>" the translatable
    block is the whole sequence: "Hello <em>baby</em>".

    0 - Ready
    1 - Skip
    2 - Hit
    """
    # FIXME This information is specific to XHTML, it should be defined at
    # a higher level, not hardcoded here.
    elements_to_skip = set(['script', 'style'])

    # Local variables
    buffer = []
    skip = 0
    hit = False
    # These two are used to uniquely identify the elements, so we can later
    # match end tags with their start tag.
    id = 0
    stack = []

    for event in events:
        type, value, line = event
        # Skip mode
        if skip > 0:
            if type == START_ELEMENT:
                skip += 1
            elif type == END_ELEMENT:
                skip -= 1
            yield event
            continue
 
        # Text node
        if type == TEXT:
            # Don't consider left whitespace
            if len(buffer) == 0 and value.strip() == '':
                yield event
                continue
            # Buffer the text node
            buffer.append(event)
            if value.strip():
                hit = True
            continue

        # Inline start element
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.get('is_inline', False):
                buffer.append((type, value + (id,), line))
                stack.append(id)
                id += 1
                continue
            # Enter skip mode
            if tag_name in elements_to_skip:
                skip = 1

        # Inline end element
        if type == END_ELEMENT:
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.get('is_inline', False):
                x = stack.pop()
                buffer.append((type, value + (x,), line))
                continue

        # Anything else: comments, block elements (start or end), etc.
        # are considered delimiters

        # Miss: the buffer is really empty
        if hit is False:
            for type, value, line in buffer:
                if type == START_ELEMENT or type == END_ELEMENT:
                    yield type, value[:-1], line
                else:
                    yield type, value, line
            yield event
            # Reset
            buffer = []
            stack = []
            id = 0
            continue

        # Process the buffer
        # Right strip
        tail = buffer[-1]
        if tail[0] == TEXT and tail[1].strip() == '':
            del buffer[-1]
            tail = [tail]
        else:
            tail = []

        # Wipe-out sourrounding elements
        while (buffer[0][0] == START_ELEMENT and buffer[-1][0] == END_ELEMENT
               and buffer[0][1][-1] == buffer[-1][1][-1]):
            type, value, line = buffer.pop(0)
            yield type, value[:-1], line
            type, value, line = buffer.pop()
            tail.insert(0, (type, value[:-1], line))

        # Remove auxiliar data
        for i in range(len(buffer)):
            type, value, line = buffer[i]
            if type == START_ELEMENT or type == END_ELEMENT:
                buffer[i] = type, value[:-1], line

        # Yield
        yield TRANSLATABLE_BLOCK, buffer, None
        for x in tail:
            yield x

        yield event
        # Reset
        hit = False
        buffer = []
        stack = []
        id = 0



def get_messages(events):
    from .xml import get_start_tag, get_end_tag

    # FIXME This information is specific to XHTML, it should be defined at
    # a higher level, not hardcoded here.
    elements_to_keep_spaces = set(['pre'])

    keep_spaces = False
    for type, value, line in get_translatable_blocks(events):
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Attributes
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                is_translatable = get_namespace(attr_uri).is_translatable
                if is_translatable(tag_uri, tag_name, attributes, attr_name):
                    if value.strip():
                        yield value, 0
            # Keep spaces
            if tag_name in elements_to_keep_spaces:
                keep_spaces = True
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            # Keep spaces
            if tag_name in elements_to_keep_spaces:
                keep_spaces = False
        elif type == TRANSLATABLE_BLOCK:
            # Build message
            message = Message()
            for type, value, line in value:
                if type == TEXT:
                    message.append_text(value)
                elif type == START_ELEMENT:
                    message.append_format(get_start_tag(*value))
                elif type == END_ELEMENT:
                    message.append_format(get_end_tag(*value))

            # Segmentation
            for segment in message.get_segments(keep_spaces):
                yield segment, 0



def translate_stack(stack, catalog, keep_spaces):
    """
    This method receives as input a stack of XML events and returns 
    another stack, the translation of the source one.
    """
    from .xml import get_start_tag, get_end_tag

    # Build the message and find out if there is something to translate
    message = Message()
    there_is_something_to_translate = False
    for event, value, line in stack:
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
        stack.append((TEXT, left, None))
    for segment in message.get_segments(keep_spaces):
        segment = catalog.get_translation(segment).encode('utf-8')
        for event, value, line in Parser(segment):
            if event == TEXT:
                value = unicode(value, 'utf-8')
            stack.append((event, value, None))
    if right:
        stack.append((TEXT, right, None))
    return stack



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
                stack.append((event, value, None))
            elif event == START_ELEMENT:
                # Inline or block
                tag_uri, tag_name, attributes = value
                schema = get_element_schema(tag_uri, tag_name)
                if schema['is_inline']:
                    stack.append((event, value, None))
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
                    yield START_ELEMENT, (tag_uri, tag_name, aux), None
                    # Presarve spaces if <pre>
                    if tag_name == 'pre':
                        keep_spaces = True
            elif event == END_ELEMENT:
                tag_uri, tag_name = value
                schema = get_element_schema(tag_uri, tag_name)
                if schema['is_inline']:
                    stack.append((event, value, None))
                else:
                    for x in translate_stack(stack, catalog, keep_spaces):
                        yield x
                    stack = []
                    # The close tag
                    yield event, value, None
                    # </pre> don't preserve spaces any more
                    if tag_name == 'pre':
                        keep_spaces = False
            else:
                yield event, value, None

        # Process trailing message
        if stack:
            for x in translate_stack(stack, catalog, keep_spaces):
                yield x


    def translate(self, catalog):
        from .xml import stream_to_str

        stream = self._translate(catalog)
        return stream_to_str(stream)
