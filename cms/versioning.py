# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2006 Hervé Cauwelier <herve@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.stl import stl
from itools.web import get_context


class VersioningAware(object):

    def commit_revision(self):
        context = get_context()
        user = context.user

        property = {
            (None, 'user'): user.name,
            ('dc', 'date'): datetime.now(),
            (None, 'size'): str(len(self.to_str())),
        }

        self.set_property('ikaaro:history', property)


    ########################################################################
    # User Interface
    ########################################################################
    history_form__access__ = 'is_allowed_to_edit'
    history_form__label__ = u'History'
    def history_form(self, context):
        namespace = {}

        revisions = []
        for revision in self.get_property('ikaaro:history'):
            username = revision[(None, 'user')]
            date = revision[('dc', 'date')]
            size = revision[(None, 'size')]
            revisions.append((date, {
                'username': username,
                'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                'size': size,
            }))

        revisions.sort(reverse=True)
        namespace['revisions'] = [r[1] for r in revisions]

        handler = self.get_handler('/ui/File_history.xml')
        return stl(handler, namespace)

