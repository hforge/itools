# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
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
from itools.gettext import MSG



class INFO(MSG):

    def __call__(self, **kw):
        if not kw:
            # Also skipping stl calls
            raise AttributeError, 'missing variables to substitute'
        message = MSG.gettext(self, language=None, **kw)
        # Send a translated copy of this instance
        return self.__class__(message, domain=self.domain)


    def gettext(self, language=None):
        # Gettext calling was defered
        return MSG.gettext(self, language=language, **self.kw)



class ERROR(INFO):
    pass



MSG_MISSING_OR_INVALID = ERROR(
    u'Some required fields are missing, or some values are not valid. '
    u'Please correct them and continue.')

