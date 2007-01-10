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
from itools.stl import stl

# Import from itools.cms
from itools.cms.registry import register_object_class
from itools.cms.Document import HTML

# Import from our package
from base import Handler


class ExampleDocument(Handler, HTML):

    class_id = 'ExampleDocument'
    class_title = u'Example Document'
    class_description = u'Here the description of our Example Document'
    class_version = '20061021'
    class_icon48 = 'frontoffice1/images/Document48.png'
    class_icon16 = 'frontoffice1/images/Document16.png'


    def get_views(self):
        views = HTML.get_views(self)
        views.append('switch_skin')

        return views


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'Preview'
    def view(self, context):
        namespace = {}
        namespace['title'] = self.get_title_or_name()
        namespace['body'] = self.to_xhtml_body()
        handler = self.get_handler('/ui/frontoffice1/ExampleDocument_view.xml')

        return stl(handler, namespace)



register_object_class(ExampleDocument)
