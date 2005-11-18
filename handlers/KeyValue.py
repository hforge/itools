# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from File import File
from Text import Text


class KeyValue(Text):

    #########################################################################
    # Parsing
    #########################################################################
    __keys__ = []
    __keys_types__ = {}

    def _load_state(self, resource):
        state = self.state

        # Initializes the keys.
        keys = set()
        for key in self.__keys__:
            if not hasattr(state, key):
                keys.add(key)
                setattr(state, key, '')

        # Parses the input data, stores the keys in self.keys and the values
        # as attributes.
        for line in resource.readlines():
            line = line.strip()
            if line:
                try:
                    key, value = line.split(':', 1)
                except ValueError:
                    pass
                else:
                    keys.add(key)
                    setattr(state, key, value)

        # Convert the values to the right type.
        for key in keys:
            value = getattr(state, key)
            type = self.__keys_types__.get(key, 'str')
            if type == 'str':
                pass
            elif type == 'unicode':
                value = unicode(value, 'utf8')
            elif type == 'bool':
                value = value.lower() == 'true'
            else:
                # XXX Error!!
                pass
            setattr(state, key, value)

        # Set state
        state.keys = keys


    #########################################################################
    # API
    #########################################################################
    def to_str(self, encoding='UTF-8'):
        data = []
        state = self.state
        for key in state.keys:
            value = getattr(state, key)
            t = self.__keys_types__.get(key, 'str')
            if t == 'str':
                pass
            elif t == 'unicode':
                value = value.encode(encoding)
            elif t == 'bool':
                value = value and 'true' or 'false'
            else:
                # XXX Error!!
                pass
            data.append('%s:%s\n' % (key, value))
        return ''.join(data)

