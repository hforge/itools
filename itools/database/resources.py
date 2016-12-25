# -*- coding: UTF-8 -*-
# Copyright (C) 2011-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from itools.core import freeze, is_prototype

# Import from itools.database
from fields import Field
from registry import register_field
from ro import RODatabase



class DBResourceMetaclass(type):

    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        if 'class_id' in dict:
            RODatabase.register_resource_class(cls)

        # Lookup fields
        if 'fields' not in dict:
            cls.fields = [ x for x in dir(cls)
                           if is_prototype(getattr(cls, x), Field) ]

        # Register new fields in the catalog
        for name in cls.fields:
            if name in dict:
                field = dict[name]
                field.name = name
                if field.indexed or field.stored:
                    datatype = field.get_datatype()
                    register_field(name, datatype)
        # Ok
        return cls



class Resource(object):

    __metaclass__ = DBResourceMetaclass
    __hash__ = None


    fields = freeze([])

    # Says what to do when a field not defined by the schema is found.
    #   soft = False: raise an exception
    #   soft = True : log a warning
    fields_soft = False


    @classmethod
    def get_field(self, name):
        if name in self.fields:
            return getattr(self, name, None)
        raise ValueError('Undefined field %s'.format(name))


    @classmethod
    def get_fields(self):
        for name in self.fields:
            field = self.get_field(name)
            if field:
                yield name, field


    def get_catalog_values(self):
        """Returns a dictionary with the values of the fields to be indexed.
        """
        raise NotImplementedError
