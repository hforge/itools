# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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



class IndexedFields(File):

    __slots__ = ['resource', 'timestamp', 'fields']


    def new(self):
        self.fields = {}


    def _load_state(self, resource):
        # Number of fields
        n_fields = resource.read(1)
        n_fields = IO.decode_byte(n_fields)

        # Load fields
        fields = {}
        data = resource.read()
        for i in range(n_fields):
            # The field number
            field_number = IO.decode_byte(data[0])
            data = data[1:]
            # The terms
            number_of_terms = IO.decode_uint32(data[:4])
            data = data[4:]
            terms = []
            for j in range(number_of_terms):
                term, data = IO.decode_string(data)
                terms.append(term)

            fields[field_number] = terms

        self.fields = fields


    def to_str(self):
        fields = self.fields

        field_numbers = fields.keys()
        field_numbers.sort()
        data = [IO.encode_byte(len(field_numbers))]

        for field_number in field_numbers:
            data.append(IO.encode_byte(field_number))
            terms = fields[field_number]
            data.append(IO.encode_uint32(len(terms)))
            for term in terms:
                data.append(IO.encode_string(term))

        return ''.join(data)


    def add_field(self, number, terms):
        self.fields[number] = terms



class StoredFields(File):
    """
    The format of this resource is:

      - number of fields (byte)
      - fields (sequence of fields)

    Where each field is:

      - field number (byte)
      - field value (string)
    """

    __slots__ = ['resource', 'timestamp', 'values', 'document']


    def new(self):
        self.values = {}
        self.document = None


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

        self.values = values

        # Cache (XXX To be replaced by the built-in state)
        self.document = None


    def to_str(self):
        values = self.values

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
        self.values[number] = value


    def get_value(self, number):
        return self.values.get(number)

