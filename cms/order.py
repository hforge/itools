# -*- coding: UTF-8 -*-
# Copyright (C) 2006 Luis Belmar-Letelier <luis@itaapy.com>
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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# Import from itools
from itools.stl import stl

# Import from itools.cms
from itools.cms.utils import comeback


class OrderAware(object):
    orderable_classes = None

    def get_catalog_indexes(self):
        document = {}
        parent = self.parent
        if isinstance(parent, OrderAware):
            index = parent.get_order_index(self)
            if index is not None:
                document['order'] = '%04d' % index

        return document


    def get_ordered_folder_names(self):
        orderable_classes = self.orderable_classes or self.__class__
        ordered_names = self.get_property('ikaaro:order')
        real_names = [f.name for f in self.search_handlers()
                if isinstance(f, orderable_classes)]

        ordered_folders = [f for f in ordered_names if f in real_names]
        unordered_folders = [f for f in real_names if f not in ordered_names]

        return ordered_folders + unordered_folders


    def get_order_index(self, folder):
        folder_name = folder.name
        ordered_names = self.get_ordered_folder_names()
        if folder_name in ordered_names:
            return ordered_names.index(folder_name)

        return None


    order_folders_form__access__ = 'is_allowed_to_edit'
    order_folders_form__sublabel__ = u"Order"
    def order_folders_form(self):
        namespace = {}
        namespace['folders'] = []

        for name in self.get_ordered_folder_names():
            folder = self.get_handler(name)
            ns = {
                'name': folder.name,
                'title': folder.get_property('dc:title', language='fr')
            }
            namespace['folders'].append(ns)

        handler = self.get_handler('/ui/Folder_order_items.xml')
        return stl(handler, namespace)


    order_folders_up__access__ = 'is_allowed_to_edit'
    def order_folders_up(self, **kw):
        if not kw.has_key('name'):
            message = u"Please select the folders to order up."
            return comeback(self.gettext(message))

        names = kw['name']
        ordered_names = self.get_ordered_folder_names()
        
        if ordered_names[0] == names[0]:
            message = u"Folders already up."
            return comeback(self.gettext(message))

        temp = list(ordered_names)
        for name in names:
            idx = temp.index(name)
            temp.remove(name)
            temp.insert(idx - 1, name)

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Folders ordered up."
        comeback(self.gettext(message))
        
        
    order_folders_down__access__ = 'is_allowed_to_edit'
    def order_folders_down(self, **kw):
        if not kw.has_key('name'):
            message = u"Please select the folders to order down."
            return comeback(message)
        
        names = kw['name']
        ordered_names = self.get_ordered_folder_names()

        if ordered_names[-1] == names[-1]:
            message = u"Folders already down."
            return comeback(self.gettext(message))
            
        temp = list(ordered_names)
        names.reverse()
        for name in names:
            idx = temp.index(name)
            temp.remove(name)
            temp.insert(idx + 1, name)

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Folders ordered down."
        comeback(self.gettext(message))
