# -*- coding: UTF-8 -*-
# Copyright (C) 2008, 2010 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2009-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2010 Hervé Cauwelier <herve@oursours.net>
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

from logging import getLogger

# Import from itools
from itools.datatypes import Boolean, Date, DateTime, Decimal, Integer
from itools.datatypes import QName, String, Time, URI
from itools.fs import lfs
from itools.handlers import TextFile, register_handler_class
from itools.uri import get_reference
from itools.xml import XMLNamespace, ElementSchema, xml_uri, xmlns_uri
from itools.xml import XMLParser, XML_DECL, START_ELEMENT, END_ELEMENT, TEXT
from itools.xml import register_namespace, has_namespace

log = getLogger("itools.core")

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
                    raise NotImplementedError(('relax NG: we implement only '
                                               'the "http://www.w3.org/2001/XMLSchema-datatypes" '
                                               'for datatypes'))


def read_name_class(context, event, stream):
    while True:
        type, value, line = event

        if type == START_ELEMENT:
            tag_uri, tag_name, attrs = value

            read_common_attrs(tag_uri, attrs, context)

            # <name> ... </name>
            if tag_name == 'name':
                # Read the content
                type, value, line = next(stream)
                if type != TEXT:
                    raise ValueError('your relax NG file is malformed')
                name = value
                # Read "</name>"
                type, value, line = next(stream)
                if (type != END_ELEMENT or value[0] != rng_uri or
                    value[1] != 'name'):
                    raise ValueError('your relax NG file is malformed')
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
                raise ValueError('your relax NG file is malformed')
        else:
            event = next(stream)


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
        return read_name_class(context, next(stream), stream)


def read_file(context, uri, file):
    uri = get_reference(uri)

    # Shortcuts
    elements = context['elements']
    references = context['references']

    # XML stream
    data_file = file.read()
    if isinstance(data_file, bytes):
        data_file = data_file.decode("utf-8")
    stream = XMLParser(data_file)
    # Parse !
    stack = []
    for xml_type, value, line in stream:

        # Set the good encoding
        if xml_type == XML_DECL:
            context['encoding'] = value[1]

        elif xml_type == START_ELEMENT:
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
                    xml_type = attrs[None, 'type']

                    last = stack[-1]
                    if last['data'] is not None:
                        last['data'] = ''
                    else:
                        last['data'] = xml_type

                # <ref>
                elif tag_name == 'ref':
                    name =  attrs[None, 'name']

                    if stack:
                        stack[-1]['refs'].append(name)

                # <define>
                elif tag_name == 'define':
                    name = attrs[None, 'name']

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
                    include_uri = uri.resolve(href)
                    include_uri = str(include_uri)
                    include_file = lfs.open(include_uri)
                    read_file(context, include_uri, include_file)

                # Ignored tags
                elif tag_name in ['grammar', 'start', 'choice',
                                  'optional', 'zeroOrMore', 'oneOrMore',
                                  'group', 'empty', 'interleave',
                                  'param', 'list', 'mixed']:
                    continue

                # Tags not implemented
                else:
                    raise NotImplementedError(f"relax NG: <{tag_name}> not implemented")
        elif xml_type == END_ELEMENT:
            tag_uri, tag_name = value
            if (tag_uri == rng_uri and
                tag_name in ['element', 'attribute', 'define']):
                stack.pop()


###########################################################################
# Schema maker
###########################################################################

# http://www.w3.org/2001/XMLSchema-datatypes
convert_type_data = {
    None: String,
    '': String,
    'string': String,
    'boolean': Boolean,
    'float': Decimal,
    'double': Decimal,
    'decimal': Decimal,
    'dateTime': DateTime,
    'duration': String,
    'hexBinary': String,
    'base64Binary': String,
    'anyURI': URI,
    'ID': String,
    'IDREF': String,
    'ENTITY': String,
    'NOTATION': String,
    'normalizedString': String,
    'token': String,
    'language': String,
    'IDREFS': String,
    'ENTITIES': String,
    'NMTOKEN': String,
    'NMTOKENS': String,
    'Name': String,
    'QName': QName,
    'NCName': String,
    'integer': Integer,
    'nonNegativeInteger': Integer,
    'positiveInteger': Integer,
    'nonPositiveInteger': Integer,
    'negativeInteger': Integer,
    'byte': Integer,
    'int': Integer,
    'long': Integer,
    'short': Integer,
    'unsignedByte': Integer,
    'unsignedInt': Integer,
    'unsignedLong': Integer,
    'unsignedShort': Integer,
    'date': Date,
    'time': Time,
    'gYearMonth': String,
    'gYear': String,
    'gMonthDay': String,
    'gDay': String,
    'gMonth': String}


def convert_type(data):
    datatype = convert_type_data.get(data)
    if datatype is not None:
        return datatype
    else:
        raise ValueError(f'relax NG: unexpected datatype "{data}"')


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
                try:
                    ref = references[ref]
                except KeyError:
                    raise KeyError(('the define "%s" is missing in your '
                                    'relax NG file') % ref)
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
                    try:
                        ref = references[ref]
                    except KeyError:
                        raise KeyError(('the define "%s" is missing in your '
                                        'relax NG file') % ref)
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
                element = ElementSchema(name=name,
                                        default_datatype=String,
                                        is_empty=is_empty,
                                        attributes=own)
                namespace['elements'][name] = element

                # Free attributes
                for (uri, name), datatype in free.items():
                    namespace = namespaces.setdefault(uri, {'elements': {},
                                                      'free_attributes': {}})
                    namespace['free_attributes'][name] = datatype

    result = {}
    prefix2uri = context['prefix']
    for namespace, data in namespaces.items():
        # Find the prefix
        for prefix, uri in prefix2uri.items():
            if uri == namespace:
                result[uri] = XMLNamespace(
                    uri=uri,
                    prefix=prefix,
                    elements=list(data['elements'].values()),
                    free_attributes=data['free_attributes'],
                    default_datatype=String)
                break
        else:
            log.warning(f'relaxng: namespace "{namespace}" not found')
    return result


###########################################################################
# The handler
###########################################################################
class RelaxNGFile(TextFile):
    """ A handler for the REgular LAnguage for XML Next Generation (RelaxNG)
    """

    class_mimetypes = ['text/x-rng']
    class_extension = 'rng'

    inline_elements = []
    skip_content_elements = []
    contexts = []

    def _load_state_from_file(self, file):
        # A new context
        context = {'encoding': 'utf-8',
                   'current_ns': None,
                   'elements': [],
                   'references': {},
                   'prefix': {}}
        context['prefix']['xml'] = xml_uri

        # Parse the file
        read_file(context, self.key, file)
        # And make the namespaces
        self.namespaces = make_namespaces(context)
        # Apply the metadata
        for uri, element_name in self.inline_elements:
            element = self.namespaces[uri].elements_kw[element_name]
            element.is_inline = True
        for uri, element_name in self.skip_content_elements:
            element = self.namespaces[uri].elements_kw[element_name]
            element.skip_content = True
        for uri, element_name, context in self.contexts:
            element = self.namespaces[uri].elements_kw[element_name]
            element.context = context



    #########################################################################
    # API Public
    #########################################################################
    def auto_register(self):
        for uri, namespace in self.namespaces.items():
            if not has_namespace(uri):
                register_namespace(namespace)


    def get_namespaces(self):
        return self.namespaces

register_handler_class(RelaxNGFile)


