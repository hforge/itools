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

# Import from itools
from itools.i18n import Message
from itools.xml import (START_ELEMENT, END_ELEMENT, TEXT, COMMENT,
                        get_namespace, get_element_schema, get_start_tag,
                        get_end_tag)


def open_tag(tag_uri, tag_name, attributes, catalog):
    """
    This method is similar to "get_start_tag", but it translates the
    attributes.
    """
    s = '<%s' % get_qname(tag_uri, tag_name)
    # The attributes
    for attr_uri, attr_name in attributes:
        value = attributes[(attr_uri, attr_name)]
        namespace = get_namespace(attr_uri)
        if namespace.is_translatable(tag_uri, tag_name, attributes, attr_name):
            value = value.strip()
            if value:
                value = catalog.get_translation(value)
        qname = get_attribute_qname(attr_uri, attr_name)
        datatype = get_datatype_by_uri(attr_uri, attr_name)
        value = datatype.encode(value)
        value = XMLAttribute.encode(value)
        s += ' %s="%s"' % (qname, value)
    # Close the start tag
    if is_empty(tag_uri, tag_name):
        s += '/>'
    else:
        s += '>'

    return s




class Translatable(object):
    """
    This mixin class provides the user interface that allows to extract
    translatable messages from an XML file, and to build a translated
    file from the origin file and a message catalog.

    The only condition for this to work is that the XML file makes the
    difference between block and inline elements (for example, XHTML).
    """

    #######################################################################
    # Extract messages
    #######################################################################
    def filter_tags(self, tags):
        skip = 0
        for event, value in self.events:
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


    def get_translatable_blocks(self):
        message = Message()
        keep_spaces = False

        for event, value in self.filter_tags(['script', 'style']):
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
                            yield Message(value), True
                # Inline or Block
                schema = get_element_schema(tag_uri, tag_name)
                if schema['is_inline']:
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
                if schema['is_inline']:
                    value = get_end_tag(tag_uri, tag_name)
                    message.append_format(value)
                else:
                    yield message, keep_spaces
                    message = Message()
                    # </pre> don't preserve spaces any more
                    if tag_name == 'pre':
                        keep_spaces = False


    def get_messages(self):
        for message, keep_spaces in self.get_translatable_blocks():
            message.normalize()
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


    #######################################################################
    # Translate
    #######################################################################
    def _translate(self, catalog):
        message = Message()
        keep_spaces = False
        stream = self.traverse()
        for event, value in stream:
            if event == TEXT:
                message.append((event, value))
            elif event == START_ELEMENT:
                # Inline or block
                tag_uri, tag_name, attributes = value
                schema = get_element_schema(tag_uri, tag_name)
                if schema['is_inline']:
                    message.append((event, value))
                    stream.send(1)
                else:
                    # Process any previous message
                    for x in process_message(message, keep_spaces):
                        buffer.write(x.encode('utf-8'))
                    message = Message()
                    # The open tag
                    buffer.write(open_tag(tag_uri, tag_name, attributes, catalog))
                    # Presarve spaces if <pre>
                    if tag_name == 'pre':
                        keep_spaces = True
            elif event == END_ELEMENT:
                tag_uri, tag_name = value
                schema = get_element_schema(tag_uri, tag_name)
                if not schema['is_inline']:
                    for x in process_message(message, keep_spaces):
                        buffer.write(x.encode('utf-8'))
                    message = Message()
                    # The close tag
                    buffer.write(get_end_tag(tag_uri, tag_name))
                    # </pre> don't preserve spaces any more
                    if tag_name == 'pre':
                        keep_spaces = False
            elif event == COMMENT:
                buffer.write('<!--%s-->' % value.encode('utf-8'))
            else:
                raise NotImplementedError

        # Process trailing message
        if message:
            for x in process_message(message, keep_spaces):
                buffer.write(x.encode('utf-8'))

        data = buffer.getvalue()
        buffer.close()
        return data


    def translate(self, catalog):
        for event, value in self._translate(catalog):
            normalize(message)
            if not message:
                return
            # Process
            if len(message) == 1 and message[0][0] == START_ELEMENT:
                node = message[0]
                buffer.write(open_tag(ns_uri, name, attributes, catalog))
                message = Message(node.children)
                for x in process_message(message, keep_spaces):
                    yield x
                yield node.get_end_tag()
            else:
                # Check wether the node message has real text to process.
                for event, value in message:
                    if event == TEXT:
                        if value.strip():
                            break
                    elif event == START_ELEMENT:
                        for event, node in x.traverse():
                            if event == TEXT:
                                if node.strip():
                                    break
                        else:
                            continue
                        break
                else:
                    # Nothing to translate
                    for event, value in message:
                        if event == TEXT:
                            yield XMLDataType.encode(value)
                        elif event == START_ELEMENT:
                            tag_uri, tag_name, attributes = value
                            buffer.write(open_tag(tag_uri, tag_name,
                                                  attributes, catalog))
                            #msg = Message(x.children)
                            #for y in process_message(msg, keep_spaces):
                            #    yield y
                        elif event == END_ELEMENT:
                            tag_uri, tag_name = value
                            yield get_end_tag(tag_uri, tag_name)
                        elif event == COMMENT:
                            yield '<!--%s-->' % value
                        else:
                            raise NotImplementedError
                    raise StopIteration
                # Something to translate: segmentation
                for segment in message.get_segments(keep_spaces):
                    msgstr = catalog.get_translation(segment)
                    # Escapes "&", except when it is an entity reference
                    def f(match):
                        x = match.group(0)
                        if x.endswith(';'):
                            return x
                        return "&amp;" + x[1:]
                    msgstr = re.sub("&[\w;]*", f, msgstr)
                    # XXX The special characters "<" and "&" must be
                    # escaped in text nodes (only in text nodes).

                    yield msgstr
                    if keep_spaces is False:
                        yield u' '
