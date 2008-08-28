# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007-2008 Sylvain Taverne <sylvain@itaapy.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
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
from itools.datatypes import Unicode, XMLContent, is_datatype
from namespaces import get_element_schema, xmlns_uri, get_attr_datatype
from parser import XMLParser, DOCUMENT_TYPE, START_ELEMENT, END_ELEMENT, TEXT
from xml import get_start_tag, get_end_tag



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
def _get_translatable_blocks(events):
    # XXX We must break this circular dependency
    from itools.srx import Message
    # XXX this constant must not be a constant
    encoding = 'utf-8'

    message = Message()
    for event in events:
        type, value, line = event

        # We catch the good events!
        if type == START_ELEMENT or type == END_ELEMENT:
            tag_uri, tag_name = value[:2]
            schema = get_element_schema(tag_uri, tag_name)
            # Inline ?
            if getattr(schema, 'is_inline', False):
                if not message:
                    message_line = line
                if type == START_ELEMENT:
                    message.append_start_format(get_start_tag(*value))
                else:
                    message.append_end_format(get_end_tag(*value))
                continue
        elif type == TEXT:
            # XXX A lonely 'empty' TEXT are ignored, is it good ?
            # Not empty ?
            if value.strip() != '' or message:
                if not message:
                    message_line = line
                value = XMLContent.encode(value)
                value = unicode(value, encoding)
                message.append_text(value)
                continue

        # Not a good event => break + send the event
        if message:
            yield MESSAGE, message, message_line
        message = Message()

        yield event
    # Send the last message!
    if message:
        yield MESSAGE, message, message_line


###########################################################################
# Get Messages
###########################################################################
def get_units(events, filename=None, srx_handler=None):
    # XXX We must break this circular dependency
    from itools.srx import get_segments
    keep_spaces = False
    for type, value, line in _get_translatable_blocks(events):
        if type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Attributes
            for attr_uri, attr_name in attributes:
                datatype = get_attr_datatype(tag_uri, tag_name, attr_uri,
                                             attr_name, attributes)
                if not is_datatype(datatype, Unicode):
                    continue
                value = attributes[(attr_uri, attr_name)]
                if not value.strip():
                    continue
                yield value, {filename: [line]}
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
            segments = get_segments(value, keep_spaces, srx_handler)
            for segment, line_offset in segments:
                yield segment, {filename: [line + line_offset]}



###########################################################################
# Translate
###########################################################################
def translate(events, catalog, srx_handler=None):
    # XXX We must break this circular dependency
    from itools.srx import translate_message
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
            # Attributes (translate)
            aux = {}
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                datatype = get_attr_datatype(tag_uri, tag_name, attr_uri,
                                             attr_name, attributes)
                if is_datatype(datatype, Unicode):
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
            translation = translate_message(value, catalog, keep_spaces,
                                            srx_handler)
            for event in XMLParser(translation, namespaces, doctype=doctype):
                yield event
        else:
            yield event

