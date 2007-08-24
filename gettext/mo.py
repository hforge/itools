# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from gettext import GNUTranslations

# Import from itools
from itools.handlers import File, register_handler_class


class MO(File):

    class_mimetypes = ['application/x-mo']
    class_extension = 'mo'

    __slots__ = ['database', 'uri', 'timestamp', 'dirty', 'parent', 'name',
                 'real_handler', 'translations']


    def _load_state_from_file(self, file):
        self.translations = GNUTranslations(file)


    def gettext(self, message):
        """
        Returns the translation for the given message.
        """
        return self.translations.ugettext(message)


register_handler_class(MO)
