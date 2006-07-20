# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from gettext import GNUTranslations

# Import from itools
from itools.handlers.File import File
from itools.handlers.registry import register_handler_class


class MO(File):

    class_mimetypes = ['application/x-mo']
    class_extension = 'mo'

    __slots__ = ['uri', 'timestamp', 'parent', 'name', 'real_handler',
                 'translations']


    def _load_state_from_file(self, file):
        self.translations = GNUTranslations(file)


    def gettext(self, message):
        return self.translations.ugettext(message)


register_handler_class(MO)
