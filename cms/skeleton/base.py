# -*- coding: UTF-8 -*-
# Copyright (C) 2004-2006 Luis Belmar-Letelier <luis@itaapy.com>
#               2006 Hervé Cauwelier <herve@oursours.net>
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA

# Import from itools
from itools import uri

# Import from itools.cms
from itools.cms.Handler import Handler as iHandler


class Handler(iHandler):

    switch_skin__access__ = 'is_allowed_to_edit'
    switch_skin__label__ = u"Switch to front-office"
    def switch_skin(self, context):
        cookie = context.get_cookie('skin_path') or 'ui/aruni'

        if cookie == 'ui/frontoffice1':
            skin_path = 'ui/aruni'
            goto = context.request.referrer
        elif cookie == 'ui/aruni':
            skin_path = 'ui/frontoffice1'
            goto = uri.get_reference(';view')

        context.set_cookie('skin_path', skin_path, path='/')

        return goto
