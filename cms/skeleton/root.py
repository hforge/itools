# -*- coding: UTF-8 -*-
# Copyright (C) YEAR(S) AUTHOR_NAME <EMAIL@ADDRESS>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.web import get_context
from itools.stl import stl

# Import from itools.cms
from itools.cms.registry import register_object_class
from itools.cms.root import Root as iRoot

# Import from our package
from base import Handler


class Root(Handler, iRoot):

    class_id = 'ExamplePortal'
    class_title = u'Example Portal'
    class_version = '20061021'
    class_domain = 'example'
    class_views = [['view']] + iRoot.class_views + [['switch_skin']]

    #_catalog_fields = ikaaroRoot._catalog_fields + [
    #        ('<field>', '<analyser>', False, True)]

    view__access__ = True
    view__label__ = u'Welcome!'
    def view(self, context):
        """ 
        A default greeting view.
        """
        handler = self.get_handler('/ui/frontoffice1/Root_view.xml')
        return stl(handler)


    def get_skin(self):
        """Set the default skin"""
        context = get_context()

        cookie = context.get_cookie('skin_path')
        if cookie == 'ui/frontoffice1':
            # return the frontoffice skin
            return self.get_handler(cookie)

        # return the default skin
        return self.get_handler('ui/aruni')


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


register_object_class(Root)
