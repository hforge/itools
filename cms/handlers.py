# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David IbÃ¡Ã±ez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from datetime import datetime
import mimetypes
from random import random
from time import time

# Import from itools
from itools.datatypes import (DateTime, QName, String, Unicode,
                              XML as XMLDataType)
from itools import schemas
from itools.handlers.File import File
from itools.handlers.Text import Text
from itools.handlers.registry import register_handler_class
from itools.xml import namespaces, parser
from itools.web import get_context
from metadata import Record



# XXX Keep for backwards compatibility (to be removed in 0.16)
class ListOfUsers(File):

    class_mimetypes = ['text/x-list-of-users']
    class_extension = 'users'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'usernames']


    def new(self, users=[]):
        self.usernames = set(users)


    def _load_state_from_file(self, file):
        self.usernames = set()
        for username in file.readlines():
            username = username.strip()
            if username:
                self.usernames.add(username)


    def to_str(self):
        return '\n'.join(self.usernames)


    def get_usernames(self):
        return self.usernames


    def add(self, username):
        self.set_changed()
        self.usernames.add(username)


    def remove(self, username):
        self.set_changed()
        self.usernames.remove(username)



class Lock(Text):

    class_mimetypes = ['text/x-lock']
    class_extension = 'lock'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'username', 'lock_timestamp', 'key']


    def new(self, username=None, **kw):
        self.username = username
        self.lock_timestamp = datetime.now()
        self.key = '%s-%s-00105A989226:%.03f' % (random(), random(), time())


    def _load_state_from_file(self, file):
        username, timestamp, key = file.read().strip().split('\n')
        self.username = username
        # XXX backwards compatibility: remove microseconds first
        timestamp = timestamp.split('.')[0]
        self.lock_timestamp = DateTime.decode(timestamp)
        self.key = key


    def to_str(self):
        timestamp = DateTime.encode(self.lock_timestamp)
        return '%s\n%s\n%s' % (self.username, timestamp, self.key)



class Metadata(File):

    class_title = u'Metadata'
    class_icon48 = 'images/File48.png'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'prefixes', 'properties']


    def new(self, handler_class=None, format=None, **kw):
        # Add format and version
        kw['format'] = format or handler_class.class_id
        kw['version'] = handler_class.class_version

        # Initialize
        properties = {}
        prefixes = set()
        # Load
        for name, value in kw.items():
            if value is None:
                continue
            # The property
            key = QName.decode(name)
            properties[key] = value
            # The prefix
            prefix = key[0]
            if prefix is not None:
                prefixes.add(prefix)

        # Set state
        self.prefixes = prefixes
        self.properties = properties


    def _load_state_from_file(self, file):
        # Keep the namespace prefixes
        self.prefixes = set()

        p_key = None
        datatype = None
        p_language = None
        p_value = ''
        stack = []
        for event, value, line_number in parser.Parser(file.read()):
            if event == parser.START_ELEMENT:
                namespace_uri, local_name, attributes, ns_decls = value
                # Update prefixes
                for ns_uri in ns_decls.values():
                    schema = schemas.get_schema_by_uri(ns_uri)
                    prefix = schema.class_prefix
                    if prefix is not None:
                        self.prefixes.add(prefix)
                if local_name == 'metadata':
                    stack.append({})
                else:
                    # Get the property type
                    schema = schemas.get_schema_by_uri(namespace_uri)
                    datatype = schema.get_datatype(local_name)
                    # Build the property key
                    p_key = (schema.class_prefix, local_name)

                    if datatype is Record:
                        stack.append({})
                    else:
                        p_value = ''

                    # xml:lang
                    attr_key = (namespaces.XMLNamespace.class_uri, 'lang')
                    p_language = attributes.get(attr_key)
            elif event == parser.END_ELEMENT:
                namespace_uri, local_name = value
                # Get the property type
                schema = schemas.get_schema_by_uri(namespace_uri)
                datatype = schema.get_datatype(local_name)
                p_default = datatype.default
                # Build the property key
                p_key = (schema.class_prefix, local_name)

                if local_name == 'metadata':
                    self.properties = stack.pop()
                else:
                    # Decode value
                    if datatype is Record:
                        p_value = stack.pop()
                    elif datatype is Unicode:
                        p_value = datatype.decode(p_value, 'UTF-8')
                    else:
                        p_value = datatype.decode(p_value)
                    # Set property
                    if isinstance(p_default, list):
                        stack[-1].setdefault(p_key, []).append(p_value)
                    elif p_language is None:
                        stack[-1][p_key] = p_value
                    else:
                        stack[-1].setdefault(p_key, {})
                        stack[-1][p_key][p_language] = p_value
                    # Reset variables
                    datatype = None
                    p_language = None
                    p_value = ''
            elif event == parser.TEXT:
                if p_key is not None:
                    p_value += value


    def to_str(self):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']

        # Insert open root element with the required namespace declarations
        if self.prefixes:
            aux = [ (x, schemas.get_schema(x).class_uri)
                    for x in self.prefixes ]
            aux = '\n          '.join([ 'xmlns:%s="%s"' % x for x in aux ])
            lines.append('<metadata %s>' % aux)
        else:
            lines.append('<metadata>')

        for key, value in self.properties.items():
            prefix, local_name = key

            # Get the type
            datatype = schemas.get_datatype(key)
            # Get the qualified name
            if prefix is None:
                qname = local_name
            else:
                qname = '%s:%s' % key

            if isinstance(value, dict):
                for language, value in value.items():
                    value = datatype.encode(value)
                    value = XMLDataType.encode(value)
                    lines.append('  <%s xml:lang="%s">%s</%s>'
                                 % (qname, language, value, qname))
            elif isinstance(value, list):
                for value in value:
                    value = datatype.encode(value)
                    if datatype is not Record:
                        value = XMLDataType.encode(value)
                    lines.append('  <%s>%s</%s>' % (qname, value, qname))
            else:
                value = datatype.encode(value)
                value = XMLDataType.encode(value)
                lines.append('  <%s>%s</%s>' % (qname, value, qname))

        lines.append('</metadata>')
        return '\n'.join(lines)


    ########################################################################
    # API
    ########################################################################
    def get_property(self, name, language=None):
        key = QName.decode(name)

        # Default value
        datatype = schemas.get_datatype(key)
        default_value = datatype.default

        if key in self.properties:
            value = self.properties[key]
        else:
            return default_value

        if isinstance(value, dict):
            # Multiple languages
            if language is None:
                # Language negotiation
                context = get_context()
                if context is None:
                    language = None
                else:
                    languages = [ k for k, v in value.items() if v.strip() ]
                    accept = context.request.accept_language
                    language = accept.select_language(languages)
                # Default (XXX pick one at random)
                if language is None:
                    language = value.keys()[0]
                return value[language]
            return value.get(language, default_value)
        return value


    def has_property(self, name, language=None):
        key = QName.decode(name)

        if key not in self.properties:
            return False

        if language is not None:
            return language in self.properties[key]

        return True


    def set_property(self, name, value, language=None):
        self.set_changed()

        key = QName.decode(name)

        # Set the value
        if language is None:
            datatype = schemas.get_datatype(key)

            default = datatype.default
            if isinstance(default, list):
                if isinstance(value, list):
                    self.properties[key] = value
                else:
                    values = self.properties.setdefault(key, [])
                    values.append(value)
            else:
                self.properties[key] = value
        else:
            values = self.properties.setdefault(key, {})
            values[language] = value

        # Update prefixes
        if key[0] is not None:
            self.prefixes.add(key[0])
        if isinstance(value, dict):
            for prefix, local_name in value:
                if prefix is not None:
                    self.prefixes.add(prefix)


    def del_property(self, name, language=None):
        key = QName.decode(name)

        if key in self.properties:
            if language is None:
                self.set_changed()
                del self.properties[key]
            else:
                values = self.properties[key]
                if language in values:
                    self.set_changed()
                    del values[language]



# Register handler classes, and mimetypes
for handler_class in [ListOfUsers, Lock, Metadata]:
    register_handler_class(handler_class)
    for mimetype in handler_class.class_mimetypes:
        mimetypes.add_type(mimetype, '.%s' % handler_class.class_extension)

mimetypes.add_type('application/x-catalog', '.catalog')
