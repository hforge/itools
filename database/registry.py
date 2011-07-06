# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

    keys = ['decode', 'encode', 'is_empty', 'default',
            'indexed', 'stored', 'multiple']
    for key in keys:
        if getattr(old, key) is not getattr(new, key):
            raise ValueError, 'register conflict over the "%s" field' % name


def get_register_fields():
    return fields_registry
