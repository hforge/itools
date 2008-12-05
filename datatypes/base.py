# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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


def is_datatype(datatype, base_type):
    """Returns True if 'datatype' is of 'base_type'.
    """
    try:
        return issubclass(datatype, base_type)
    except TypeError:
        return isinstance(datatype, base_type)


def copy_datatype(datatype, **kw):
    # Class
    if type(datatype) is type:
        return datatype(**kw)

    # Instance
    # FIXME Use 'merge_dics'
    dict = datatype.__dict__.copy()
    for key in kw:
        dict[key] = kw[key]
    return datatype.__class__(**kw)



class DataType(object):

    # Default value
    default = None

    # I18n part
    context = None


    def __init__(self, **kw):
        for key in kw:
            setattr(self, key, kw[key])


    @classmethod
    def get_default(cls):
        default = cls.default
        if getattr(cls, 'multiple', False) is True:
            if isinstance(default, list):
                return list(default)
            else:
                # Change "default" explicitely to have an initialized list
                return []
        return default


    @staticmethod
    def decode(data):
        """Deserializes the given byte string to a value with a type.
        """
        raise NotImplementedError


    @staticmethod
    def encode(value):
        """Serializes the given value to a byte string.
        """
        raise NotImplementedError


    @staticmethod
    def is_valid(value):
        """Checks whether the given value is valid.

        For example, for a natural number the value will be an integer, and
        this method will check that it is not a negative number.
        """
        return True


    @staticmethod
    def is_empty(value):
        """Checks whether the given value is empty or not.

        For example, a text string made of white spaces may be considered
        as empty.  (NOTE This is used by the multilingual code.)
        """
        return value is None
