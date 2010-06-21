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
    if name in fields_registry:
        if fields_registry[name] is field_cls:
            return
        raise ValueError, 'register conflict over the "%s" field' % name

    fields_registry[name] = field_cls


def get_register_fields():
    return fields_registry
