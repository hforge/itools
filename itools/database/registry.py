# Copyright (C) 2010-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from types import MethodType

fields_registry = {}


def register_field(name, field_cls):
    if name not in fields_registry:
        fields_registry[name] = field_cls
        return

    # Error?
    old = fields_registry[name]
    new = field_cls
    if old is new:
        return

    keys = ['default', 'indexed', 'stored', 'multiple',
            'decode', 'encode', 'is_empty']
    for key in keys:
        old_value = getattr(old, key, None)
        new_value = getattr(new, key, None)
        if type(old_value) is MethodType:
            old_value = old_value.__func__
        if type(new_value) is MethodType:
            new_value = new_value.__func__

        if old_value != new_value:
            msg = 'register conflict over the "{0}" field ({1} is different)'
            raise ValueError(msg.format(name, key))


def get_register_fields():
    return fields_registry
