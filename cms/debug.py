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

# Import from itools
from itools.xml.stl import stl

# Import from itools.cms
from utils import comeback


class Folder(object):

    manage_content__access__ = 'is_admin'
    def manage_content(self):
        namespace = {}
        resources = []
        for name in self.resource.get_resource_names():
            resources.append({'href': '%s/;manage_content' % name,
                              'name': name})
        namespace['resources'] = resources

        handler = self.get_handler('/ui/Folder_manage_content.xml')
        return stl(handler, namespace)



class Text(object):

    manage_content__access__ = 'is_admin'
    def manage_content(self):
        namespace = {}
        namespace['data'] = self.resource.read()

        handler = self.get_handler('/ui/Text_manage_content.xml')
        return stl(handler, namespace)


    manage_edit__access__ = 'is_admin'
    def manage_edit(self, data, **kw):
        self.set_data(data)
        message = self.gettext(u'Changes saved.')
        comeback(message)
