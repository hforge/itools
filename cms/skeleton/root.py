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
from itools.web import get_context
from itools.stl import stl

# Import from itools.cms
from itools.cms.registry import register_object_class
from itools.cms.root import Root as iRoot

# Import from our package
from base import Handler
from folder import ExampleFolder


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


    def get_document_types(self):
        types = iRoot.get_document_types(self)
        return types + [ExampleFolder]



register_object_class(Root)
