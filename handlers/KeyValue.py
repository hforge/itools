# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from Python
import sets

# Import from itools
from File import File
from Text import Text




class KeyValue(Text):


    #########################################################################
    # Parsing
    #########################################################################
    __keys__ = []
    __keys_types__ = {}

    def _load(self, resource):
        File._load(self, resource)

        # Initializes the keys.
        self.keys = sets.Set()
        for key in self.__keys__:
            if not hasattr(self, key):
                self.keys.add(key)
                setattr(self, key, '')

        # Parses the input data, stores the keys in self.keys and the values
        # as attributes.
        data = self._data
        del self._data

        # Parse
        for line in data.split('\n'):
            line = line.strip()
            if line:
                try:
                    key, value = line.split(':', 1)
                except ValueError:
                    pass
                else:
                    self.keys.add(key)
                    setattr(self, key, value)

        # Convert the values to the right type.
        for key in self.keys:
            value = getattr(self, key)
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
            setattr(self, key, value)



    #########################################################################
    # API
    #########################################################################
    def to_unicode(self):
        data = u''
        for key in self.keys:
            value = getattr(self, key)
            t = self.__keys_types__.get(key, 'str')
            if t == 'str':
                value = unicode(value)
            elif t == 'unicode':
                pass
            elif t == 'bool':
                value = value and u'true' or u'false'
            else:
                # XXX Error!!
                pass
            data += u'%s:%s\n' % (key, value)
        return data

