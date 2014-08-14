# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Matthieu France <matthieu@itaapy.com>
# Copyright (C) 2008, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008, 2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2010 Henry Obein <henry.obein@gmail.com>
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
from itools.stl import stl, stl_namespaces
from itools.xml import XMLParser


class INFO(MSG):

    css = 'info'

    def _format(self, message, **kw):
        if self.format == 'stl':
            events = XMLParser(message.encode('utf_8'),
                               namespaces=stl_namespaces)
            return stl(events=events, namespace=self)

        return super(INFO, self)._format(message, **kw)



class ERROR(INFO):

    css = 'error'



MSG_MISSING_OR_INVALID = ERROR(
    u'Some required fields are missing, or some values are not valid. '
    u'Please correct them and continue.')
