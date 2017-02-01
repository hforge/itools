# -*- coding: UTF-8 -*-
# Copyright (C) 2011-2012 J. David Ibáñez <jdavid.ibp@gmail.com>
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
from itools.core import is_prototype, merge_dicts, prototype
from itools.gettext import MSG
from itools.validators import validator


class Field(prototype):

    name = None
    title = None
    datatype = None
    indexed = False
    stored = False
    multiple = False
    empty_values = (None, '', [], (), {})
    base_error_messages = {
        'invalid': MSG(u'Invalid value.'),
        'required': MSG(u'This field is required.'),
    }
    error_messages = {}
    validators = []


    def get_datatype(self):
        return self.datatype


    def access(self, mode, resource):
        # mode may be "read" or "write"
        return True


    def get_validators(self):
        validators = []
        for v in self.validators:
              if type(v) is str:
                  v = validator(v)()
              validators.append(v)
        return validators


    def get_error_message(self, code):
        messages = merge_dicts(
            self.base_error_messages,
            self.error_messages)
        return messages.get(code)



def get_field_and_datatype(elt):
    """ Now schema can be Datatype or Field.
    To be compatible:
      - we return datatype if a field is given
      - we build a field if a datatype is given

    """
    if is_prototype(elt, Field):
        return elt, elt.get_datatype()
    return Field(datatype=elt), elt
