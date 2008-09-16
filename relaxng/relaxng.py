# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
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
from itools.handlers import TextFile, register_handler_class
from itools.xml import XMLParser, XML_DECL, START_ELEMENT, END_ELEMENT, TEXT
from itools.xml import XMLNamespace, ElementSchema, xmlns_uri
from itools.xml import register_namespace
from itools.xml.namespaces import has_namespace
from itools.datatypes import (Date, DateTime, Decimal, Integer, QName,
                              String, Time, Unicode, URI)
from itools import vfs
import itools.http


# Namespace of Relax NG
rng_uri = 'http://relaxng.org/ns/structure/1.0'


###########################################################################
# Relax Analyser
###########################################################################
def read_common_attrs(tag_uri, attrs, context):
    for uri, name in attrs:
        # A prefix declaration ?
        if uri == xmlns_uri:
            value = attrs[uri, name]
            context['prefix'][name] = value
        # XXX: we appromixate the current namespace as the last ns found
        if tag_uri == rng_uri and uri is None:
            value = attrs[uri, name]
            if name == 'ns':
                context['default_ns'] = value
            elif name == 'datatypeLibrary':
                if value != 'http://www.w3.org/2001/XMLSchema-datatypes':
                    raise NotImplementedError, ('relax NG: we implement only '
                       'the "http://www.w3.org/2001/XMLSchema-datatypes" '
                       'for datatypes')


def read_name_class(context, event, stream):
    while True:
        type, value, line = event

        if type == START_ELEMENT:
            tag_uri, tag_name, attrs = value

            read_common_attrs(tag_uri, attrs, context)

            # <name> ... </name>
            if tag_name == 'name':
                # Read the content
                type, value, line = stream.next()
                if type != TEXT:
                    raise ValueError, 'your relax NG file is malformed'
                name = value
                # Read "</name>"
                type, value, line = stream.next()
                if (type != END_ELEMENT or value[0] != rng_uri or
                    value[1] != 'name'):
                    raise ValueError, 'your relax NG file is malformed'
                # Make Qname
                if ':' in name:
                    prefix, trash, name = name.partition(':')
                    uri = context['prefix'][prefix]
                    return [(uri, name)]
                else:
                    uri = context['default_ns']
                    return [(uri, name)]

            # <choice> ... </choice>
            elif tag_name == 'choice':
                qnames = []
                for event in stream:
                    type, value, line = event
                    if type ==  TEXT:
                        continue
                    elif type == START_ELEMENT:
                        qnames.extend(read_name_class(context, event, stream))
                    elif type == END_ELEMENT and value[1] == 'choice':
                        return qnames

            # We ignore the tags 'anyName' and 'nsName' and return None
            elif tag_name in ['anyName', 'nsName']:
                level = 1
                for type, value, line in stream:
                    if type == START_ELEMENT:
                        tag_uri, tag_name, attrs = value
                        read_common_attrs(tag_uri, attrs, context)
                        level += 1
                    elif type == END_ELEMENT:
                        level -= 1
                        if level == 0:
                            return None
            else:
                raise ValueError, 'your relax NG file is malformed'
        else:
            event = stream.next()


def read_qnames(attrs, context, stream):
    # Embedded uri/name
    if (None, 'name') in  attrs:
        name = attrs[None, 'name']
        if ':' in name:
            prefix, trash, name = name.partition(':')
            uri = context['prefix'][prefix]
            return [(uri, name)]
        else:
            uri = context['current_ns']
            return [(uri, name)]
    # In the next events, ...
    else:
        return read_name_class(context, stream.next(), stream)


def read_file(context, file):
    # Shortcuts
    elements = context['elements']
    references = context['references']

    # XML stream
    stream = XMLParser(file.read())

    # Parse !
    stack = []
    for type, value, line in stream:
        # Set the good encoding
        if type == XML_DECL:
            context['encoding'] = value[1]

        elif type == START_ELEMENT:
            tag_uri, tag_name, attrs = value

            # Set your context variable
            read_common_attrs(tag_uri, attrs, context)

            # Only RNG !
            if tag_uri == rng_uri:

                # <element>
                if tag_name == 'element':
                    # Create a new element
                    qnames = read_qnames(attrs, context, stream)
                    element = {'qnames': qnames,
                               'attributes': [],
                               'data': None,
                               'is_empty': True,
                               'refs': []}

                    # My father has at least a child,  me!
                    if stack:
                        stack[-1]['is_empty'] = False

                    # And push it
                    elements.append(element)
                    stack.append(element)

                # <attribute>
                elif tag_name == 'attribute':
                    # Create a new attribute
                    qnames = read_qnames(attrs, context, stream)
                    attribute = {'qnames': qnames,
                                 'data': None,
                                 'refs': []}

                    # And push it
                    stack[-1]['attributes'].append(attribute)
                    stack.append(attribute)

                # <data>
                elif tag_name == 'data':
                    type = attrs[None, 'type']

                    last = stack[-1]
                    if last['data'] is not None:
                        last['data'] = ''
                    else:
                        last['data'] = type

                # <ref>
                elif tag_name == 'ref':
                    name =  attrs[None, 'name']

                    if stack:
                        stack[-1]['refs'].append(name)

                # <define>
                elif tag_name == 'define':
                    name =  attrs[None, 'name']

                    # New or merge ?
                    if name in references and (None, 'combine') in attrs:
                        ref = references[name]
                    else:
                        ref = {'attributes': [],
                               'data': None,
                               'is_empty': True,
                               'refs': []}
                        references[name] = ref

                    stack.append(ref)

                # <text>
                elif tag_name == 'text':
                    last = stack[-1]
                    if last['data'] is not None:
                        last['data'] = ''
                    else:
                        last['data'] = 'string'

                # <value>
                elif tag_name == 'value':
                    stack[-1]['data'] = ''

                # <include>
                elif tag_name == 'include':
                    href = attrs[None, 'href']
                    include_file = vfs.open(href)
                    read_file(context, include_file)

                # Ignored tags
                elif tag_name in ['grammar', 'start', 'choice',
                                  'optional', 'zeroOrMore', 'oneOrMore',
                                  'group', 'empty', 'interleave',
                                  'param', 'list', 'mixed']:
                    continue

                # Tags not implemented
                else:
                    raise NotImplementedError, ('relax NG: <%s> not '
                          'implemented') % tag_name
        elif type == END_ELEMENT:
            tag_uri, tag_name = value
            if (tag_uri == rng_uri and
                tag_name in ['element', 'attribute', 'define']):
                    stack.pop()


###########################################################################
# Schema maker
###########################################################################

# http://www.w3.org/2001/XMLSchema-datatypes
def convert_type(data):
    # None, default => string
    if data is None or data == 'string':
        return String
    # Complex data => string
    elif data == '':
        return String
    elif data in ['integer', 'nonNegativeInteger', 'positiveInteger',
                'nonPositiveInteger', 'negativeInteger']:
        return Integer
    elif data in ['float', 'double', 'decimal']:
        return Decimal
    elif data == 'time':
        return Time
    elif data == 'date':
        return Date
    elif data == 'dateTime':
        return DateTime
    elif data in ['gYearMonth', 'gYear', 'gMonthDay', 'gDay', 'gMonth']:
        return String
    elif data == 'boolean':
        return Boolean
    elif data == 'anyURI':
        return URI
    elif data == 'QName':
        return QName
    elif data in ['byte', 'int', 'long', 'short', 'unsignedByte',
                  'unsignedInt', 'unsignedLong', 'unsignedShort']:
        return Integer
    elif data in ['hexBinary', 'base64Binary']:
        return String
    # Remains, ...
    elif data in ['duration', 'ID', 'IDREF', 'ENTITY', 'NOTATION',
                  'normalizedString', 'token', 'language', 'IDREFS',
                  'ENTITIES', 'NMTOKEN', 'NMTOKENS', 'Name', 'NCName']:
        return String
    else:
        raise ValueError, 'relax NG: unexpected datatype "%s"' % data


def split_attributes(uri, attributes):
    own = {}
    free = {}
    for attribute in attributes:
        qnames = attribute['qnames']
        datatype = convert_type(attribute['data'])
        if qnames is not None:
            for qname in qnames:
                if uri != qname[0]:
                    free[qname] = datatype
                else:
                    own[qname[1]] = datatype
    return own, free


def make_namespaces(context):
    # Shortcuts
    elements = context['elements']
    references = context['references']

    # Find all namespaces, and fill them with elements
    namespaces = {}
    for element in elements:
        qnames = element['qnames']
        attributes = element['attributes']
        data = element['data']
        is_empty = element['is_empty']
        refs = element['refs']

        # Replace the references of "refs"
        while refs:
            new_refs = []
            for ref in refs:
                ref = references[ref]
                attributes.extend(ref['attributes'])
                new_refs.extend(ref['refs'])
                is_empty = is_empty and ref['is_empty']

                ref_data = ref['data']
                if ref_data is not None:
                    if data is not None and data != ref_data:
                        data = ''
                    elif data is None:
                        data = ref_data

            refs = new_refs

        # Now, data is good
        if data is not None:
            is_empty = False

        # Replace the references of "attributes"
        for attribute in attributes:
            refs = attribute['refs']
            while refs:
                new_refs = []
                for ref in refs:
                    ref = references[ref]
                    new_refs.extend(ref['refs'])

                    ref_data = ref['data']
                    attr_data = attribute['data']

                    if ref_data is not None:
                        if attr_data is not None and attr_data != ref_data:
                            attr_data = ''
                        elif attr_data is None:
                            attr_data = ref_data

                refs = new_refs

        # Update the good namespaces
        if qnames is not None:
            for uri, name in element['qnames']:
                own, free = split_attributes(uri, attributes)

                # Element + its attributes
                namespace = namespaces.setdefault(uri, {'elements': {},
                                                  'free_attributes': {}})
                element = ElementSchema(name,
                                        default_datatype=String,
                                        is_empty=is_empty,
                                        attributes=own)
                namespace['elements'][name] = element

                # Free attributes
                for (uri, name), datatype in free.iteritems():
                    namespace = namespaces.setdefault(uri, {'elements': {},
                                                      'free_attributes': {}})
                    namespace['free_attributes'][name] = datatype

    result = []
    prefix2uri = context['prefix']
    for namespace, data in namespaces.iteritems():
        # Find the prefix
        for prefix, uri in prefix2uri.iteritems():
            if uri == namespace:
                break
        result.append(XMLNamespace(uri, prefix, data['elements'].values(),
                      data['free_attributes'], String))
    return result


###########################################################################
# The handler
###########################################################################
class RelaxNGFile(TextFile):
    """ A handler for the REgular LAnguage for XML Next Generation (RelaxNG)
    """

    class_mimetypes = ['text/x-rng']
    class_extension = 'rng'

    def _load_state_from_file(self, file):
        # A new context
        context = {'encoding' : 'utf-8',
                   'current_ns' : None,
                   'elements': [],
                   'references': {},
                   'prefix' : {}}

        # Parse the file
        read_file(context, file)

        # And make the namespaces
        self.namespaces = make_namespaces(context)



    #########################################################################
    # API Public
    #########################################################################
    def auto_register(self):
        for namespace in self.namespaces:
            if not has_namespace(namespace.uri):
                register_namespace(namespace)

register_handler_class(RelaxNGFile)


