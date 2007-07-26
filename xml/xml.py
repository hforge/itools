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
from itools.datatypes import XMLAttribute, XML as XMLContent
from itools.schemas import get_datatype_by_uri
from itools.handlers import Text, register_handler_class
from i18n import get_messages, translate
from namespaces import get_namespace, is_empty, XMLNSNamespace
from parser import (Parser, XML_DECL, DOCUMENT_TYPE, START_ELEMENT,
                    END_ELEMENT, TEXT, COMMENT, CDATA)


# FIXME Current implementation regarding XML namespaces for attributes
# does not respectes the standard, and needs therefore be changed.
# Specifically, unprefixed attributes do not inherit the namspace from
# the element.
#
# See http://lists.xml.org/archives/xml-dev/200505/msg00091.html for
# an elightement discussion.
#
# The modules affected include the parser, and probably the namespace API.


#############################################################################
# Data types
#############################################################################

# Serialize
def get_qname(ns_uri, name):
    """Returns the fully qualified name"""
    if ns_uri is None:
        return name
    prefix = get_namespace(ns_uri).class_prefix
    if prefix is None:
        return name
    return '%s:%s' % (prefix, name)


def get_attribute_qname(namespace, local_name):
    """Returns the fully qualified name"""
    if namespace is None:
        return local_name

    prefix = get_namespace(namespace).class_prefix
    if prefix is None:
        return local_name

    # Namespace declarations for the default namespace lack the local
    # name (e.g. xmlns="http://www.example.org"). Here 'xmlns' is always
    # the prefix, and there is not a local name. This an special case.
    if local_name is None:
        return prefix

    return '%s:%s' % (prefix, local_name)


def get_start_tag(tag_uri, tag_name, attributes):
    s = '<%s' % get_qname(tag_uri, tag_name)
    # Output the attributes
    for attr_uri, attr_name in attributes:
        value = attributes[(attr_uri, attr_name)]
        datatype = get_datatype_by_uri(attr_uri, attr_name)
        qname = get_attribute_qname(attr_uri, attr_name)
        value = XMLAttribute.encode(value)
        s += ' %s="%s"' % (qname, value)
    # Close the start tag
    if is_empty(tag_uri, tag_name):
        return s + '/>'
    else:
        return s + '>'


def get_end_tag(ns_uri, name):
    if is_empty(ns_uri, name):
        return ''
    return '</%s>' % get_qname(ns_uri, name)


def stream_to_str(stream, encoding='UTF-8'):
    data = []
    for event, value, line in stream:
        if event == TEXT:
            value = XMLContent.encode(value)
            data.append(value)
        elif event == START_ELEMENT:
            ns_uri, name, attributes = value
            data.append(get_start_tag(ns_uri, name, attributes))
        elif event == END_ELEMENT:
            ns_uri, name = value
            data.append(get_end_tag(ns_uri, name))
        elif event == COMMENT:
            data.append('<!--%s-->' % value)
        elif event == XML_DECL:
            version, encoding, standalone = value
            if standalone is None:
                data.append('<?xml version="%s" encoding="%s"?>'
                    % (version, encoding))
            else:
                data.append(
                    '<?xml version="%s" encoding="%s" standalone="%s"?>'
                    % (version, encoding, standalone))
        elif event == DOCUMENT_TYPE:
            name, system_id, public_id, has_internal_subset = value
            if public_id is None:
                data.append('<!DOCTYPE %s SYSTEM "%s">' % (name, system_id))
            elif system_id is None:
                # XXX Special case for HTML (not good XML)
                data.append('<!DOCTYPE %s PUBLIC "%s">' % (name, public_id))
            else:
                data.append('<!DOCTYPE %s PUBLIC "%s"\n  "%s">'
                    % (name, public_id, system_id))
        elif event == CDATA:
            data.append('<![CDATA[%s]]>' % value)
        else:
            raise NotImplementedError, 'unknown event "%s"' % event
    return ''.join(data)



def find_end(events, start):
    """Receives a list of events and a position in the list of an start
    element.

    Returns the position in the list where the element ends.
    """
    c = 1
    n = len(events)
    i = start + 1
    while i < n:
        event, value, line = events[i]
        if event == START_ELEMENT:
            c += 1
        elif event == END_ELEMENT:
            c -= 1
            if c == 0:
                return i
        i = i + 1
    return None


def get_element(events, name):
    i = 0
    for event, value, line in events:
        if event == START_ELEMENT:
            if name == value[1]:
                return Element(events, i)
        i += 1
    return None


class Element(object):

    __slots__ = ['events', 'start', 'end']

    def __init__(self, events, start):
        self.events = events
        self.start = start
        self.end = find_end(events, start)


    def get_content_elements(self):
        events = self.events

        i = self.start + 1
        while i < self.end:
            yield events[i]
            i += 1


    def get_content(self, encoding='UTF-8'):
        return stream_to_str(self.get_content_elements())


    def get_content_as_html(self, encoding='UTF-8'):
        from itools.xhtml import stream_to_str_as_html
        return stream_to_str_as_html(self.get_content_elements())




#############################################################################
# Documents
#############################################################################
class Document(Text):
    """
    An XML file is represented in memory as a tree where the nodes are
    instances of the classes 'Element' and 'Raw'. The 'Element' class
    represents an XML element, the 'Raw' class represents a text string.

    XML sub-classes will, usually, provide their specific semantics by
    providing their own Element and Raw classes. This is the reason why
    we use 'self.Element' and 'self.Raw' throghout the code instead of
    just 'Element' and 'Raw'.
    """

    class_mimetypes = ['text/xml', 'application/xml']
    class_extension = 'xml'


    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'events']


    def new(self):
        # XML is a meta-language, it does not make change to create a bare
        # XML handler without a resource.
        raise NotImplementedError
    
    
    def _load_state_from_file(self, file):
        data = file.read()
        stream = Parser(data)
        self.events = list(stream)


    #######################################################################
    # API
    #######################################################################
    def to_str(self, encoding='UTF-8'):
        return stream_to_str(self.events, encoding)


    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return 1
        return cmp(self.__dict__, other.__dict__)


    def to_text(self):
        """
        Removes the markup and returns a plain text string.
        """
        text = [ unicode(value, 'utf-8') for event, value, line in self.events
                 if event == TEXT ]
        return u' '.join(text)


    #######################################################################
    # API / Internationalization - Localization
    #######################################################################
    def get_messages(self):
        return get_messages(self.events)


    def translate(self, catalog):
        stream = translate(self.events, catalog)
        return stream_to_str(stream)


register_handler_class(Document)
