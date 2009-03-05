# -*- coding: UTF-8 -*-
# Copyright (C) 2008 David Versmisse <david.versmisse@itaapy.com>
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from xapian
from xapian import sortable_serialise, sortable_unserialise

# Import from itools
from itools.datatypes import Integer


def _decode(field_cls, data):
    """Used to decode values in stored fields.
    """
    # Overload the Integer type, cf _encode
    if issubclass(field_cls, Integer):
        if data == '':
            return None
        return int(sortable_unserialise(data))
    # A common field or a new field
    return field_cls.decode(data)



# We must overload the normal behaviour (range + optimization)
def _encode(field_cls, value):
    """Used to encode values in stored fields.
    """
    # Overload the Integer type
    # XXX warning: this doesn't work with the big integers!
    if issubclass(field_cls, Integer):
        return sortable_serialise(value)
    # A common field or a new field
    return field_cls.encode(value)



def _get_field_cls(name, fields, info):
    return fields[name] if (name in fields) else fields[info['from']]



