# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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

# Import from itools
from itools.gettext import Message as gettextMessage
from itools.datatypes import XMLContent
from itools.i18n import Message
from itools.i18n.segment import get_segments, translate_message
from namespaces import get_element_schema, xmlns_uri
from parser import XMLParser, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT



###########################################################################
# Constants
###########################################################################
MESSAGE = 999

# FIXME This information is specific to XHTML, it should be defined at
# a higher level, not hardcoded here.
elements_to_keep_spaces = set(['pre'])


###########################################################################
# Code common to "get_units" and "translate"
###########################################################################
def _process_buffer(buffer, hit, encoding):
    from xml import get_start_tag, get_end_tag

    # Miss: the buffer is really empty
    if hit is False:
        for type, value, line in buffer:
            if type == START_ELEMENT or type == END_ELEMENT:
                yield type, value[:-1], line
            else:
                yield type, value, line
        return

    # Process the buffer
    # Right strip
    tail = buffer[-1]
    if tail[0] == TEXT and tail[1].strip() == '':
        del buffer[-1]
        tail = [tail]
    else:
        tail = []

    # Remove auxiliar data
    for i in range(len(buffer)):
        type, value, line = buffer[i]
        if type == START_ELEMENT or type == END_ELEMENT:
            buffer[i] = type, value[:-1], line

    # Build message
    first_line = None
    if buffer:
        type, value, first_line = buffer[0]
    message = Message()
    for type, value, line in buffer:
        if type == TEXT:
            value = XMLContent.encode(value)
            value = unicode(value, encoding)
            message.append_text(value)
        elif type == START_ELEMENT:
            message.append_start_format(get_start_tag(*value))
        elif type == END_ELEMENT:
            message.append_end_format(get_end_tag(*value))

    # Return message
    yield MESSAGE, message, first_line

    # Return tail
    for x in tail:
        yield x



def _get_translatable_blocks(events):
    """This method is defined so it can be used by both "get_units" and
    "translate". Hence it contains the logic that is commont to both, to avoid
    code duplication.

    It returns back the events it receives, except that it finds out when a
    sequence of events defines a translatable block. Then this block sequence
    is returned, identified by an special event type (MESSAGE).

    A translatable block is one that:

      - contains at least one non-empty text node;
      - does not contain block-elements;

    We also do not consider sourronding inline-elements. For example, in
    "<em>Hello baby</em>" the translatable block is just the text node "Hello
    baby". But in "Hello <em>baby</em>" the translatable block is the whole
    sequence: "Hello <em>baby</em>".
    """
    # Local variables
    encoding = 'utf-8' # FIXME hardcoded
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
            if getattr(schema, 'is_inline', False) or stack:
                buffer.append((type, value + (id,), line))
                stack.append(id)
                id += 1
                continue
            # Enter skip mode
            if not schema.translate_content:
                skip = 1

        # Inline end element
        if type == END_ELEMENT:
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if getattr(schema, 'is_inline', False) or stack:
                x = stack.pop()
                buffer.append((type, value + (x,), line))
                continue

        # Anything else: comments, block elements (start or end), etc.
        # are considered delimiters
        for x in _process_buffer(buffer, hit, encoding):
            yield x

        yield event

        # Reset
        hit = False
        buffer = []
        stack = []
        id = 0

    for x in _process_buffer(buffer, hit, encoding):
        yield x


###########################################################################
# Get Messages
###########################################################################
def get_units(events, filename=None):
    keep_spaces = False
    for type, value, line in _get_translatable_blocks(events):
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            element = get_element_schema(tag_uri, tag_name)
            # Attributes
            for attr_uri, attr_name in attributes:
                if not element.is_translatable(attributes, attr_name):
                    continue
                value = attributes[(attr_uri, attr_name)]
                if not value.strip():
                    continue
                yield gettextMessage([], [value], [u''], {filename: [line]})
            # Keep spaces
            if tag_name in elements_to_keep_spaces:
                keep_spaces = True
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            # Keep spaces
            if tag_name in elements_to_keep_spaces:
                keep_spaces = False
        elif type == MESSAGE:
            # Segmentation
            for segment, line_offset in get_segments(value, keep_spaces):
                yield gettextMessage([], [segment], [u''],
                                     {filename: [line + line_offset]})



###########################################################################
# Translate
###########################################################################
def translate(events, catalog):
    encoding = 'utf-8' # FIXME hardcoded
    doctype = None
    keep_spaces = False
    namespaces = {}
    for event in _get_translatable_blocks(events):
        type, value, line = event
        if type == DOCUMENT_TYPE:
            name, doctype = value
        elif type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            element = get_element_schema(tag_uri, tag_name)
            # Attributes (translate)
            aux = {}
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                if element.is_translatable(attributes, attr_name):
                    value = value.strip()
                    if value:
                        value = catalog.gettext(value)
                        value = value.encode(encoding)
                aux[(attr_uri, attr_name)] = value
                # Namespaces
                # FIXME We must support xmlns="...." too.
                # FIXME We must consider the end of the declaration
                if attr_uri == xmlns_uri:
                    namespaces[attr_name] = value
            yield START_ELEMENT, (tag_uri, tag_name, aux), None
            # Keep spaces
            if tag_name in elements_to_keep_spaces:
                keep_spaces = True
        elif type == END_ELEMENT:
            yield event
            # Keep spaces
            tag_uri, tag_name = value
            if tag_name in elements_to_keep_spaces:
                keep_spaces = False
        elif type == MESSAGE:
            translation = translate_message(value, catalog, keep_spaces)
            for event in XMLParser(translation, namespaces, doctype=doctype):
                yield event
        else:
            yield event

