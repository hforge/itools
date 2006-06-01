# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.handlers.Text import Text



class Config(Text):

    class_extension = None

    
    def get_skeleton(self, **kw):
        lines = [ '%s = %s' % x for x in kw.items() ]
        return '\n'.join(lines)


    def _load_state(self, resource):
        values = {}
        lines = []
        for line in resource.readlines():
            line = line.strip()
            lines.append(line)
            if line and not line.startswith('#'):
                name, value = line.split('=', 1)
                name = name.strip()
                value = value.strip()
                values[name] = value

        state = self.state
        state.lines = lines
        state.values = values


    def to_str(self):
        values = self.state.values

        names = values.keys()

        lines = []
        for line in self.state.lines:
            if line and not line.startswith('#'):
                name, value = line.split('=', 1)
                name = name.strip()
                if name in values:
                    value = values[name]
                    names.remove(name)
                else:
                    value = value.strip()
                line = '%s = %s' % (name, value)

            lines.append(line)

        # Append new values
        for name in names:
            lines.append('%s = %s' % (name, values[name]))

        return '\n'.join(lines)


    #########################################################################
    # API
    #########################################################################
    def set_value(self, name, value):
        self.set_changed()
        self.state.values[name] = value


    def get_value(self, name):
        return self.state.values.get(name)


    def has_value(self, name):
        return name in self.state.values
