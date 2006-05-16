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

# Import from the Standard Library
from operator import attrgetter

# Import from itools
from itools.stl import stl
from itools.web import get_context

# Import from itools.cms
from itools.cms.utils import comeback
from itools.cms.Group import ListOfUsers


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
            return comeback(self.gettext(message))
        
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



class RoleAware(object):

    __roles__ = [
        {'name': 'members', 'title': u"Members", 'unit': u"Member"},
        {'name': 'reviewers', 'title': u"Reviewers", 'unit': u"Reviewer"},
    ]


    def get_roles(self):
        return list(self.__roles__)


    def get_role_names(self):
        return [r['name'] for r in self.__roles__]


    def get_role_resource_names(self):
        return ['.%s' % r for r in self.get_role_names()]


    def get_skeleton(self, **kw):
        skeleton = {}

        # build roles
        for role in self.get_roles():
            rolename = role['name']
            users = kw.get(rolename, [])
            skeleton['.%s' % rolename] = ListOfUsers(users=users)

        return skeleton


    def _get_handler(self, segment, resource):
        return ListOfUsers(resource)


    def is_in_role(self, rolename, username=None):
        if username is None:
            context = get_context()
            user = context.user
            if user is None:
                return False
            username = user.name

        role = self.get_handler('.%s' % rolename)
        return username in role.get_usernames()


    def del_roles(self, username):
        for role in self.get_roles():
            handler = self.get_handler('.%s' % role['name'])
            if username in handler.get_usernames():
                handler.remove(username)

        context = get_context()
        root = context.root
        try:
            user = root.get_user(username)
            user.clear_group_cache()
        except LookupError:
            pass


    def set_role(self, rolename, username):
        for role in self.get_roles():
            handler = self.get_handler('.%s' % role['name'])
            if rolename == role['name']:
                if not username in handler.get_usernames():
                    handler.add(username)
            else:
                if username in handler.get_usernames():
                    handler.remove(username)

        context = get_context()
        root = context.root
        try:
            user = root.get_user(username)
            user.clear_group_cache()
        except LookupError:
            pass


    #########################################################################
    # User Interface
    def get_roles_namespace(self, username):
        namespace = []

        for role in self.get_roles():
            rolename = role['name']
            namespace.append({
                'name': rolename,
                'title': self.gettext(role['unit']),
                'selected': self.is_in_role(rolename, username)
            })

        return namespace


    def get_views(self):
        return ['permissions_form']


    def _get_members_sort_key(self):
        return 'title_or_name'


    permissions_form__access__ = 'is_allowed_to_edit'
    permissions_form__label__ = u"Permissions"
    def permissions_form(self):
        context = get_context()
        root = context.root
        userfolder = root.get_handler('users')
        namespace = {}

        members = set()
        for role in self.get_roles():
            rolename = role['name']
            handler = self.get_handler('.%s' % rolename)
            members = members.union(handler.get_usernames())

        users = []
        for member in members:
            try:
                user = userfolder.get_handler(member)
            except LookupError:
                continue
            users.append(user)
        key = attrgetter(self._get_members_sort_key())
        users.sort(key=key)
        namespace['users'] = []

        for user in users:
            username = user.name
            info = {}
            info['name'] = username
            info['title'] = user.get_title_or_name()
            info['roles'] = self.get_roles_namespace(username)
            namespace['users'].append(info)

        others = []
        for user in userfolder.search_handlers():
            if user.name not in members:
                others.append(user)
        others.sort(key=key)

        namespace['others'] = []
        for user in others:
            info = {}
            info['name'] = user.name
            info['title'] = user.get_title_or_name()
            namespace['others'].append(info)

        handler = self.get_handler('/ui/Folder_permissions.xml')
        return stl(handler, namespace)


    permissions__access__ = 'is_allowed_to_edit'
    def permissions(self, delusers=[], addusers=[], **kw):
        context = get_context()
        root = context.root

        # permissions to remove
        if kw.get('delete'):
            if isinstance(delusers, str):
                delusers = [delusers]
            for username in delusers:
                self.del_roles(username)

            message = self.gettext(u"Members deleted.")
            return comeback(message)

        # permissions to add
        elif kw.get('add'):
            if isinstance(addusers, str):
                addusers = [addusers]
            for username in addusers:
                self.set_role('members', username)

            message = self.gettext(u"Members added.")
            return comeback(message)

        # permissions to change
        elif kw.get('update'):
            userfolder = root.get_handler('users')
            for username, new_role in kw.items():
                if username in delusers or (
                    username in addusers or (
                        not userfolder.has_handler(username))):
                    continue
                self.set_role(new_role, username)

            message = self.gettext(u"Roles updated.")
            return comeback(message)
