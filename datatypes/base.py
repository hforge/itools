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

# Import from the Standard Library
from warnings import warn


def is_datatype(datatype, base_type):
    # TODO To be removed by 0.60
    warn("The 'is_datatype' function is deprecated.")
    return issubclass(datatype, base_type)


def copy_datatype(datatype, **kw):
    # TODO To be removed by 0.60
    warn("The 'copy_datatype' function is deprecated.")
    return datatype(**kw)



class DataType(object):

    # Default value
    default = None
    multiple = False


    def __new__(cls, **kw):
        class_name = "%s(%s)" % (cls.__name__, kw)
        new_datatype = type(class_name, (cls,), kw)
        for key, value in kw.iteritems():
            setattr(new_datatype, key, value)
        return new_datatype


    @classmethod
    def get_default(cls):
        default = cls.default
        if cls.multiple:
            if isinstance(default, list):
                return list(default)
            # Change "default" explicitly to have an initialized list
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


    @classmethod
    def split(cls, value):
        """To index a field it must be split in a sequence of words and
        positions:

          [(word, 0), (word, 1), (word, 2), ...]

        Where <word> will be a <str> value. Usually this function will be a
        generator.
        """
        if cls.multiple:
            if isinstance(value, (tuple, list, set, frozenset)):
                for position, x in enumerate(value):
                    yield cls.encode(x), position
            else:
                yield cls.encode(value), 0
        else:
            yield cls.encode(value), 0


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
