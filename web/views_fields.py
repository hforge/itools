# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from itools
from itools.core import thingy, thingy_property
from itools.datatypes import String
from itools.gettext import MSG
from exceptions import FormError



class ViewField(thingy):

    name = None
    source = 'form' # Possible values: query & form
    datatype = String
    readonly = False
    required = False

    # Output values for the 'cook' method
    value = None
    error = None

    # Error messages
    error_required = MSG(u'This field is required.')
    error_invalid = MSG(u'Invalid value.')


    def __init__(self, name=None, **kw):
        if name and not self.name:
            self.name = name


    @thingy_property
    def multiple(self):
        return self.datatype.multiple


    def get_default(self):
        return self.datatype.get_default()


    def cook(self, source, required=None):
        if required is None:
            required = self.required
        value = source.get(self.name)

        # Case 1: missing
        if value is None:
            if required:
                self.error = self.error_required
            else:
                self.value = self.get_default()
            return

        # Case 2: multiple
        datatype = self.datatype
        if self.multiple:
            if type(value) is not list:
                value = [value]
            # Decode
            try:
                values = [ datatype.decode(x) for x in value ]
            except Exception:
                self.error = self.error_invalid
                return
            # Validate
            for value in values:
                if not datatype.is_valid(value):
                    self.error = self.error_invalid
                    return
            self.value = values
            return

        # Case 3: singleton
        if type(value) is list:
            value = value[0]
        # Decode
        try:
            value = datatype.decode(value)
        except Exception:
            self.error = self.error_invalid
            return

        # If value is None or it is a blank string, we consider it is missing
        # (XXX fragile)
        missing = (
            value is None
            or isinstance(value, basestring) and not value.strip())
        if missing:
            if required:
                self.error = self.error_required
            else:
                self.value = self.get_default()
            return

        # Validate
        if not datatype.is_valid(value):
            self.error = self.error_invalid

        # Ok
        self.value = value

