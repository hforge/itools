# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007-2008 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2008 Romain Gauthier <romain.gauthier@itaapy.com>
# Copyright (C) 2008 Wynand Winterbach <wynand.winterbach@gmail.com>
# Copyright (C) 2008-2009 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from itools.datatypes import Unicode, XMLContent, XMLAttribute
from itools.srx import Message, get_segments, translate_message
from itools.srx import TEXT as srx_TEXT
from itools.xml import get_element_schema, xmlns_uri, get_attr_datatype
from itools.xml import is_empty, get_qname, get_attribute_qname, get_end_tag
from itools.xml import XMLParser, XMLError, DOCUMENT_TYPE, XML_DECL
from itools.xml import START_ELEMENT, END_ELEMENT, TEXT, COMMENT
from itools.xml import stream_to_str
from itools.xmlfile.errors import TranslationError



# Constants
MESSAGE = 999


###########################################################################
# Common code to "get_units" and "translate"
###########################################################################
def _get_attr_context(datatype, tag_name, attr_name):
    context = getattr(datatype, 'context', None)

    # By default, the context of attribute is "element[name]"
    if context is None:
        return '%s[%s]' % (tag_name, attr_name)

    return context


def _make_start_format(tag_uri, tag_name, attributes, encoding):
    # We must search for translatable attributes
    result = [('<%s' % get_qname(tag_uri, tag_name), False, None)]

    for attr_uri, attr_name in attributes:
        qname = get_attribute_qname(attr_uri, attr_name)

        qname = Unicode.decode(qname, encoding=encoding)
        value = attributes[(attr_uri, attr_name)]
        value = Unicode.decode(value, encoding=encoding)
        value = XMLAttribute.encode(value)

        datatype = get_attr_datatype(tag_uri, tag_name, attr_uri, attr_name,
                                     attributes)
        if issubclass(datatype, Unicode):
            result[-1] = (result[-1][0] + ' %s="' % qname, False, None)
            context = _get_attr_context(datatype, tag_name, attr_name)
            result.append((value, True, context))
            result.append(('"', False, None))
        else:
            result[-1] = (result[-1][0] + ' %s="%s"' % (qname, value), False, None)
    # Close the start tag
    if is_empty(tag_uri, tag_name):
        result[-1] = (result[-1][0] + '/>', False, None)
    else:
        result[-1] = (result[-1][0] + '>', False, None)

    return result



def _get_translatable_blocks(events):
    # Default value
    encoding = 'utf-8'

    # To identify the begin/end format
    id = 0
    id_stack = []
    context_stack = [None]
    stream = None

    message = Message()
    skip_level = 0
    for event in events:
        xml_type, value, line = event
        # Set the good encoding
        if xml_type == XML_DECL:
            encoding = value[1]
        # And now, we catch only the good events
        elif xml_type == START_ELEMENT:
            if skip_level > 0:
                skip_level += 1
                if stream:
                    stream.append(event)
                    continue
            else:
                tag_uri, tag_name, attributes = value
                schema = get_element_schema(tag_uri, tag_name)
                # Context management
                if schema.context is not None:
                    context_stack.append(schema.context)

                # Skip content ?
                if schema.skip_content:
                    skip_level = 1
                    if id_stack:
                        stream = [event]
                        continue
                # Is inline ?
                elif schema.is_inline:
                    id += 1
                    id_stack.append(id)

                    start_format = _make_start_format(tag_uri, tag_name,
                                                      attributes, encoding)
                    message.append_start_format(start_format, id, line)
                    continue
                elif id_stack:
                    skip_level = 1
                    stream = [event]
                    continue
        elif xml_type == END_ELEMENT:
            if skip_level > 0:
                skip_level -= 1
                if stream:
                    stream.append(event)
                    if skip_level == 0:
                        id += 1
                        aux = stream_to_str(stream, encoding)
                        aux = [(aux, False, context_stack[-1])]
                        message.append_start_format(aux, id, line)
                        message.append_end_format([], id, line)
                        stream = None
                    continue
            else:
                tag_uri, tag_name = value[:2]
                schema = get_element_schema(tag_uri, tag_name)

                # Context management
                if schema.context is not None:
                    context_stack.pop()

                # Is inline ?
                if schema.is_inline:
                    message.append_end_format([(get_end_tag(value), False,
                                                None)], id_stack.pop(), line)
                    continue
        elif xml_type == TEXT:
            # Not empty ?
            if stream:
                stream.append(event)
                continue
            elif skip_level == 0 and (value.strip() != '' or message):
                value = XMLContent.encode(value)
                message.append_text(value, line, context_stack[-1])
                continue
        elif xml_type == COMMENT:
            if stream:
                stream.append(event)
                continue
            elif message:
                id += 1
                value = '<!--%s-->' % value
                message.append_start_format([(value, False, None)], id, line)
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
    keep_spaces = False
    keep_spaces_level = 0
    for xml_type, value, line in _get_translatable_blocks(events):
        if xml_type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Attributes
            for attr_uri, attr_name in attributes:
                datatype = get_attr_datatype(tag_uri, tag_name, attr_uri,
                                             attr_name, attributes)
                if not issubclass(datatype, Unicode):
                    continue
                value = attributes[(attr_uri, attr_name)]
                value = datatype.decode(value)
                if not value.strip():
                    continue
                unit = ((srx_TEXT, value),)
                yield (unit, _get_attr_context(datatype, tag_name, attr_name),
                       line)
            # Keep spaces ?
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces = True
                keep_spaces_level += 1
        elif xml_type == END_ELEMENT:
            # Keep spaces ?
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces_level -= 1
                if keep_spaces_level == 0:
                    keep_spaces = False
        elif xml_type == MESSAGE:
            # Segmentation
            for segment in get_segments(value, keep_spaces, srx_handler):
                yield segment



###########################################################################
# Translate
###########################################################################
def translate(events, catalog, srx_handler=None):
    # Default values
    encoding = 'utf-8'
    doctype = None
    keep_spaces = False
    keep_spaces_level = 0
    namespaces = {}

    for event in _get_translatable_blocks(events):
        xml_type, value, line = event
        # Set the good encoding
        if xml_type == XML_DECL:
            encoding = value[1]
            yield event
        # Store the current DTD
        elif xml_type == DOCUMENT_TYPE:
            name, doctype = value
            yield event
        # GO !
        elif xml_type == START_ELEMENT:
            tag_uri, tag_name, attributes = value
            # Attributes (translate)
            for attr_uri, attr_name in attributes:
                value = attributes[(attr_uri, attr_name)]
                datatype = get_attr_datatype(tag_uri, tag_name, attr_uri,
                                             attr_name, attributes)
                if issubclass(datatype, Unicode):
                    value = value.strip()
                    if value:
                        value = datatype.decode(value, encoding)
                        unit = ((srx_TEXT, value),)
                        context = _get_attr_context(datatype,tag_name,
                                                    attr_name)
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
        elif xml_type == END_ELEMENT:
            yield event
            # Keep spaces ?
            tag_uri, tag_name = value
            schema = get_element_schema(tag_uri, tag_name)
            if schema.keep_spaces:
                keep_spaces_level -= 1
                if keep_spaces_level == 0:
                    keep_spaces = False
        elif xml_type == MESSAGE:
            try:
                translation = translate_message(value, catalog, keep_spaces,
                                                srx_handler)
            except KeyError:
                # translate_message can raise an KeyError in case of translations mistake
                raise TranslationError(line=line)
            try:
                for event in XMLParser(translation,
                                       namespaces, doctype=doctype):
                    yield event
            except XMLError:
                raise XMLError(('please have a look in your source file, '
                                'line ~ %d:\n%s') % (line, value.to_str()))
        else:
            yield event
