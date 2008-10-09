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
from itools.datatypes import Unicode, XMLContent, XMLAttribute, is_datatype
from namespaces import get_element_schema, xmlns_uri, get_attr_datatype
from namespaces import is_empty
from parser import XMLParser, XMLError, DOCUMENT_TYPE, XML_DECL
from parser import START_ELEMENT, END_ELEMENT, TEXT, COMMENT
from xml import get_qname, get_attribute_qname, get_end_tag


###########################################################################
# Constants
###########################################################################
MESSAGE = 999


###########################################################################
# Common code to "get_units" and "translate"
###########################################################################
def _get_attr_context(tag_name, attr_name):
    # By default, the context of attribute is "element[name]"
    return '%s[%s]' % (tag_name, attr_name)


def _make_start_format(tag_uri, tag_name, attributes):
    # We must search for translatable attributes
    result = [(u'<%s' % get_qname(tag_uri, tag_name),
               False, None)]

    for attr_uri, attr_name in attributes:
        value = attributes[(attr_uri, attr_name)]
        qname = get_attribute_qname(attr_uri, attr_name)
        value = XMLAttribute.encode(value)

        datatype = get_attr_datatype(tag_uri, tag_name, attr_uri, attr_name,
                                     attributes)
        if is_datatype(datatype, Unicode):
            result.append((u' %s="' % qname, False, None))
            context = _get_attr_context(tag_name, attr_name)
            result.append((u'%s' % value, True, context))
            result.append((u'"', False, None))
        else:
            result.append((u' %s="%s"' % (qname, value),
                            False, None))
    # Close the start tag
    if is_empty(tag_uri, tag_name):
        result.append((u'/>', False, None))
    else:
        result.append((u'>', False, None))

    return result



def _get_translatable_blocks(events):
    # XXX We must break this circular dependency
    from itools.srx import Message

    # Default value
    encoding = 'utf-8'

    # To identify the begin/end format
    id = 0
    id_stack = []
    context_stack = [None]

    message = Message()
    skip_level = 0
    for event in events:
        type, value, line = event

        # Set the good encoding
        if type == XML_DECL:
            encoding = value[1]
        # And now, we catch only the good events
        elif type == START_ELEMENT:
            if skip_level > 0:
                skip_level += 1
            else:
                tag_uri, tag_name, attributes = value
                schema = get_element_schema(tag_uri, tag_name)

                # Context management
                if schema.context is not None:
                    context_stack.append(schema.context)

                # Skip content ?
                if schema.skip_content:
                    skip_level = 1
                # Is inline ?
                elif schema.is_inline:
                    id += 1
                    id_stack.append(id)

                    start_format = _make_start_format(tag_uri, tag_name,
                                                      attributes)
                    message.append_start_format(start_format, id, line)
                    continue
        elif type == END_ELEMENT:
            if skip_level > 0:
                skip_level -= 1
            else:
                tag_uri, tag_name = value[:2]
                schema = get_element_schema(tag_uri, tag_name)

                # Context management
                if schema.context is not None:
                    context_stack.pop()

                # Is inline ?
                if schema.is_inline:
                    message.append_end_format([(get_end_tag(*value), False,
                                                None)], id_stack.pop(), line)
                    continue
        elif type == TEXT:
            # Not empty ?
            if skip_level == 0 and (value.strip() != '' or message):
                value = XMLContent.encode(value)
                value = unicode(value, encoding)
                message.append_text(value, line, context_stack[-1])
                continue
        elif type == COMMENT and message:
            id += 1
            message.append_start_format([('<!--%s-->' % value, False, None)],
                                        id, line)
            message.append_end_format([], id, line)
            continue

        # Not a good event => break + send the event
        if message:
            yield MESSAGE, message, message.get_line()
            message = Message()

        yield event
    # Send the last message!
    if message:
        yield MESSAGE, message, message.get_line()


###########################################################################
# Get Messages
###########################################################################
def get_units(events, srx_handler=None):
    # XXX We must break this circular dependency
    from itools.srx import get_segments, TEXT as srx_TEXT

    keep_spaces = False
    keep_spaces_level = 0
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
                unit = ((srx_TEXT, value),)
                yield unit, _get_attr_context(tag_name, attr_name), line
            # Keep spaces ?
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces = True
                keep_spaces_level += 1
        elif type == END_ELEMENT:
            # Keep spaces ?
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces_level -= 1
                if keep_spaces_level == 0:
                    keep_spaces = False
        elif type == MESSAGE:
            # Segmentation
            for segment in get_segments(value, keep_spaces, srx_handler):
                yield segment



###########################################################################
# Translate
###########################################################################
def translate(events, catalog, srx_handler=None):
    # XXX We must break this circular dependency
    from itools.srx import translate_message, TEXT as srx_TEXT

    # Default values
    encoding = 'utf-8'
    doctype = None
    keep_spaces = False
    keep_spaces_level = 0
    namespaces = {}

    for event in _get_translatable_blocks(events):
        type, value, line = event

        # Set the good encoding
        if type == XML_DECL:
            encoding = value[1]
            yield event
        # Store the current DTD
        elif type == DOCUMENT_TYPE:
            name, doctype = value
            yield event
        # GO !
        elif type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Attributes (translate)
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                datatype = get_attr_datatype(tag_uri, tag_name, attr_uri,
                                             attr_name, attributes)
                if is_datatype(datatype, Unicode):
                    value = value.strip()
                    if value:
                        unit = ((srx_TEXT, value),)
                        context = _get_attr_context(tag_name, attr_name)
                        unit = catalog.gettext(unit, context)
                        value = unit[0][1]
                        value = value.encode(encoding)
                        attributes[(attr_uri, attr_name)] = value
                # Namespaces
                # FIXME We must support xmlns="...." too.
                # FIXME We must consider the end of the declaration
                if attr_uri == xmlns_uri:
                    namespaces[attr_name] = value
            yield START_ELEMENT, (tag_uri, tag_name, attributes), None
            # Keep spaces ?
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces = True
                keep_spaces_level += 1
        elif type == END_ELEMENT:
            yield event
            # Keep spaces ?
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces_level -= 1
                if keep_spaces_level == 0:
                    keep_spaces = False
        elif type == MESSAGE:
            translation = translate_message(value, catalog, keep_spaces,
                                            srx_handler)
            try:
                for event in XMLParser(translation.encode(encoding),
                                       namespaces, doctype=doctype):
                    yield event
            except XMLError:
                raise XMLError, ('please have a look in your source file, '
                                 'line ~ %d:\n%s') % (line, value.to_str())
        else:
            yield event

