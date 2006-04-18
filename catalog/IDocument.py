# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import datetime

# Import from itools
from itools.handlers.File import File
from itools.handlers.Folder import Folder
import IO



class IndexedField(File):

    def get_skeleton(self):
        return IO.encode_uint32(0)


    def _load_state(self, resource):
        state = self.state

        state.number_of_terms = IO.decode_uint32(resource.read(4))
        state.terms = []

        data = resource.read()
        for i in range(state.number_of_terms):
            term, data = IO.decode_string(data)
            state.terms.append(term)


    def add_term(self, term):
        state = self.state

        state.number_of_terms += 1
        state.terms.append(term)
        # Update the resource
        self.resource.write(IO.encode_uint32(state.number_of_terms))
        self.resource.append(IO.encode_string(term))
        # Set timestamp
        self.timestamp = self.resource.get_mtime()


    def to_str(self):
        state = self.state
        return IO.encode_uint32(state.number_of_terms) \
               + ''.join([ IO.encode_string(x) for x in state.terms ])



class StoredFields(File):

    def get_skeleton(self):
        return IO.encode_byte(0)


    def _load_state(self, resource):
        data = resource.read()

        # Read number of fields
        n_fields = IO.decode_byte(data[0])
        data = data[1:]

        # Load fields
        values = {}
        for i in range(n_fields):
            field_number = IO.decode_byte(data[0])
            data = data[1:]
            field_value, data = IO.decode_string(data)
            values[field_number] = field_value

        self.state.values = values


    def to_str(self):
        values = self.state.values

        # Field numbers
        field_numbers = values.keys()
        field_numbers.sort()

        # Number of fields
        n_fields = len(field_numbers)
        data = [IO.encode_byte(n_fields)]

        # Fields
        for field_number in field_numbers:
            field_value = values[field_number]
            data.append(IO.encode_byte(field_number))
            data.append(IO.encode_string(field_value))

        return ''.join(data)


    def set_value(self, number, value):
        self.state.values[number] = value


    def get_value(self, number):
        return self.state.values.get(number)



class IDocument(Folder):

    def get_skeleton(self):
        return {'stored': StoredFields()}


    def _get_handler(self, segment, resource):
        name = segment.name
        if name.startswith('i'):
            return IndexedField(resource)
        elif name == 'stored':
            return StoredFields(resource)
        return Folder._get_handler(self, segment, resource)


    def _load_state(self, resource):
        Folder._load_state(self, resource)
        self.document = None


    # Used by Catalog.index_document, may be removed (XXX).
    def _set_handler(self, name, handler):
        self.resource.set_resource(name, handler.resource)
        self.state.cache[name] = None
        self.timestamp = self.resource.get_mtime()


