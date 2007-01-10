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
from itools.cms.Folder import Folder
from itools.cms.File import File

# Import from our package
from base import Handler
from document import ExampleDocument


class ExampleFolder(Handler, Folder):

    class_id = 'ExampleFolder'
    class_title = u'Example Folder'
    class_description = u'Here the description of our Example Folder'
    class_version = '20061021'
    class_icon48 = 'frontoffice1/images/Folder48.png'
    class_icon16 = 'frontoffice1/images/Folder16.png'
    class_views = Folder.class_views + [['view'], ['switch_skin']]


    def get_document_types(self):
         return [ExampleFolder, ExampleDocument, File]


    view__access__ = 'is_allowed_to_view'
    view__label__ = u'Preview'
    def view(self, context):
        namespace = {}
        namespace['title'] = self.get_title_or_name()

        documents = []
        for document in self.search_handlers(format='ExampleDocument', state='public'):
            documents.append({
                'path': '%s/;view' % document.name,
                'title': document.get_title_or_name(),
                'mtime': document.get_mtime().strftime("%Y-%m-%d %H:%M")})
        namespace['documents'] = documents

        handler = self.get_handler('/ui/frontoffice1/ExampleFolder_view.xml')
        return stl(handler, namespace)



register_object_class(ExampleFolder)
