# -*- coding: UTF-8 -*-
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

# Import from the Standard Library
from datetime import datetime

# Import from itools
from itools.csv import escape_data, fold_line
from itools.datatypes import Unicode



class BaseCalendar(object):
    """Base class for the different calendar formats.
    """

    def generate_uid(self, c_type='UNKNOWN'):
        """Generate a uid based on c_type and current datetime.
        """
        return ' '.join([c_type, datetime.now().isoformat()])


    def encode_property(self, name, property_values, encoding='utf-8'):
        if not isinstance(property_values, list):
            property_values = [property_values]

        datatype = self.get_datatype(name)

        lines = []
        for property_value in property_values:
            # The parameters
            parameters = ''
            for param_name in property_value.parameters:
                param_value = property_value.parameters[param_name]
                parameters += ';%s=%s' % (param_name, ','.join(param_value))

            # The value (encode)
            value = property_value.value
            if isinstance(datatype, Unicode):
                value = datatype.encode(value, encoding=encoding)
            else:
                value = datatype.encode(value)
            # The value (escape)
            value = escape_data(value)

            # Build the line
            line = '%s%s:%s\n' % (name, parameters, value)

            # Append
            lines.append(fold_line(line))

        return lines

