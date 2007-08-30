# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from operator import itemgetter

# Import from itools
from itools.i18n import format_datetime
from itools.stl import stl
from itools.web import get_context


class VersioningAware(object):

    def commit_revision(self):
        context = get_context()
        username = ''
        if context is not None:
            user = context.user
            if user is not None:
                username = user.name

        property = {
            (None, 'user'): username,
            ('dc', 'date'): datetime.now(),
            (None, 'size'): str(len(self.to_str())),
        }

        self.set_property('ikaaro:history', property)


    def get_revisions(self, context):
        accept = context.get_accept_language()
        revisions = []

        for revision in self.get_property('ikaaro:history'):
            username = revision[(None, 'user')]
            date = revision[('dc', 'date')]
            size = revision[(None, 'size')]
            revisions.append({
                'username': username,
                'date': format_datetime(date, accept=accept),
                'sort_date': date,
                'size': size})

        revisions.sort(key=itemgetter('sort_date'), reverse=True)
        return revisions


    ########################################################################
    # User Interface
    ########################################################################
    history_form__access__ = 'is_allowed_to_view'
    history_form__label__ = u'History'
    def history_form(self, context):
        namespace = {}

        namespace['revisions'] = self.get_revisions(context)

        handler = self.get_object('/ui/file/history.xml')
        return stl(handler, namespace)

