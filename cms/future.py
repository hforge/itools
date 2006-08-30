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



class OrderAware(object):
    orderable_classes = None

    def get_ordered_folder_names(self):
        "Return current order plus the unordered names at the end."
        orderable_classes = self.orderable_classes or self.__class__
        ordered_names = self.get_property('ikaaro:order')
        real_names = [f.name for f in self.search_handlers()
                if isinstance(f, orderable_classes)]

        ordered_folders = [f for f in ordered_names if f in real_names]
        unordered_folders = [f for f in real_names if f not in ordered_names]

        return ordered_folders + unordered_folders


    def get_ordered_objects(self, objects):
        "Return a sorted list of child handlers or brains of them."
        ordered_list = []
        ordered_names = self.get_ordered_folder_names()
        for object in objects:
            index = ordered_names.index(object.name)
            ordered_list.append((index, object))

        ordered_list.sort()

        return [x[1] for x in ordered_list]


    order_folders_form__access__ = 'is_allowed_to_edit'
    order_folders_form__label__ = u"Order"
    order_folders_form__sublabel__ = u"Order"
    def order_folders_form(self, context):
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
    def order_folders_up(self, context):
        names = context.get_form_values('names')
        if not names:
            return context.come_back(u"Please select the folders to order up.")

        ordered_names = self.get_ordered_folder_names()
        
        if ordered_names[0] == names[0]:
            return context.come_back(u"Folders already up.")

        temp = list(ordered_names)
        for name in names:
            idx = temp.index(name)
            temp.remove(name)
            temp.insert(idx - 1, name)

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Folders ordered up."
        return context.come_back(message)
        
        
    order_folders_down__access__ = 'is_allowed_to_edit'
    def order_folders_down(self, context):
        names = context.get_form_values('names')
        if not names:
            return context.come_back(
                u"Please select the folders to order down.")
        
        ordered_names = self.get_ordered_folder_names()

        if ordered_names[-1] == names[-1]:
            return context.come_back(u"Folders already down.")
            
        temp = list(ordered_names)
        names.reverse()
        for name in names:
            idx = temp.index(name)
            temp.remove(name)
            temp.insert(idx + 1, name)

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Folders ordered down."
        return context.come_back(message)


    order_folders_top__access__ = 'is_allowed_to_edit'
    def order_folders_top(self, context):
        names = context.get_form_values('names')
        if not names:
            message = u"Please select the folders to order on top."
            return context.come_back(message)

        ordered_names = self.get_ordered_folder_names()
        
        if ordered_names[0] == names[0]:
            message = u"Folders already on top."
            return context.come_back(message)

        temp = names + [name for name in ordered_names
                if name not in names]

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Folders ordered on top."
        return context.come_back(message)
        
        
    order_folders_bottom__access__ = 'is_allowed_to_edit'
    def order_folders_bottom(self, context):
        names = context.get_form_values('names')
        if not names:
            message = u"Please select the folders to order on bottom."
            return context.come_back(message)

        ordered_names = self.get_ordered_folder_names()
        
        if ordered_names[-1] == names[-1]:
            message = u"Folders already on bottom."
            return context.come_back(message)

        temp = [name for name in ordered_names
                if name not in names] + names

        self.set_property('ikaaro:order', tuple(temp))
        message = u"Folders ordered on bottom."
        return context.come_back(message)
