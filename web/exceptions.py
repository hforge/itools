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
from itools.core import freeze
from itools.gettext import MSG
from messages import ERROR



class FormError(StandardError):
    """Raised when a form is invalid (missing or invalid fields).
    """

    def __init__(self, message=None, missing=freeze([]), invalid=freeze([])):
        self.msg = message
        self.missing = missing
        self.invalid = invalid


    def get_message(self):
        # Custom message
        if self.msg is not None:
            if isinstance(self.msg, MSG):
                return self.msg
            return ERROR(self.msg)
        # Default message
        missing = len(self.missing)
        invalid = len(self.invalid)
        if missing and invalid:
            msg = u"There are {miss} field(s) missing and {inv} invalid."
        elif missing:
            msg = u"There are {miss} field(s) missing."
        elif invalid:
            msg = u"There are {inv} field(s) invalid."
        else:
            # We should never be here
            msg = u"Everything looks fine (strange)."

        # Ok
        return ERROR(msg, miss=missing, inv=invalid)


    def __str__(self):
        return self.get_message().gettext()



