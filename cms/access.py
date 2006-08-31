# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
from operator import attrgetter

# Import from itools
from itools.web import get_context
from itools.web.access import AccessControl as AccessControlBase
from itools.stl import stl
from handlers import ListOfUsers
from Folder import Folder


class AccessControl(AccessControlBase):

    def is_admin(self, user, object=None):
        if user is None:
            return False
        return get_context().root.is_in_role('admins', user.name)


    def is_allowed_to_view(self, user, object):
        # Objects with workflow
        from workflow import WorkflowAware
        if isinstance(self, WorkflowAware):
            state = self.workflow_state
            # Anybody can see public objects
            if state == 'public':
                return True

            # Only those who can edit are allowed to see non-public objects
            return self.is_allowed_to_edit(user, object)

        # Everybody can see objects without workflow
        return True


    def is_allowed_to_edit(self, user, object):
        # By default only the admin can touch stuff
        return self.is_admin(user)


    # By default all other change operations (add, remove, copy, etc.)
    # are equivalent to "edit".
    def is_allowed_to_add(self, user, object):
        return self.is_allowed_to_edit(user, object)


    def is_allowed_to_remove(self, user, object):
        return self.is_allowed_to_edit(user, object)


    def is_allowed_to_copy(self, user, object):
        return self.is_allowed_to_edit(user, object)


    def is_allowed_to_move(self, user, object):
        return self.is_allowed_to_edit(user, object)


    def is_allowed_to_trans(self, user, object, name):
        return self.is_allowed_to_edit(user, object)



class RoleAware(AccessControl, Folder):
    """
    This base class implements access control based on the concept of roles.
    Includes a user interface.
    """

    #########################################################################
    # Access Control
    #########################################################################
    def is_allowed_to_edit(self, user, object):
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user):
            return True

        # Reviewers and Members are allowed to edit
        if self.is_in_role('reviewers'):
            return True
        if self.is_in_role('members'):
            return True

        return False


    def is_allowed_to_trans(self, user, object, name):
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user):
            return True

        # Reviewers can do everything
        if self.is_in_role('reviewers'):
            return True

        # Members only can request and retract
        if self.is_in_role('members'):
            return name in ('request', 'unrequest')

        return False


    #########################################################################
    # To override
    #########################################################################
    __roles__ = [
        {'name': 'members', 'title': u"Members", 'unit': u"Member"},
        {'name': 'reviewers', 'title': u"Reviewers", 'unit': u"Reviewer"},
    ]


    #########################################################################
    # API
    #########################################################################
    def _get_handler(self, segment, uri):
        name = segment.name
        if name.endswith('.users'):
            return ListOfUsers(uri)
        return Folder._get_handler(self, segment, uri)


    def has_role(self, name):
        for role in self.__roles__:
            if role['name'] == name:
                return True
        return False


    def get_role(self, name):
        return self.get_handler('.%s.users' % name)


    def get_roles(self):
        return list(self.__roles__)


    def get_role_names(self):
        return [r['name'] for r in self.__roles__]


    def get_role_resource_names(self):
        return ['.%s.users' % r for r in self.get_role_names()]


    def new(self, **kw):
        Folder.new(self)
        cache = self.cache
        for role in self.get_roles():
            rolename = role['name']
            users = kw.get(rolename, [])
            cache['.%s.users' % rolename] = ListOfUsers(users=users)


    def is_in_role(self, rolename, username=None):
        if username is None:
            context = get_context()
            user = context.user
            if user is None:
                return False
            username = user.name

        if self.has_role(rolename):
            role = self.get_role(rolename)
            return username in role.get_usernames()
        return False


    def del_roles(self, username):
        for role in self.get_roles():
            handler = self.get_role(role['name'])
            if username in handler.get_usernames():
                handler.remove(username)


    def set_role(self, rolename, username):
        for role in self.get_roles():
            handler = self.get_role(role['name'])
            if rolename == role['name']:
                if not username in handler.get_usernames():
                    handler.add(username)
            else:
                if username in handler.get_usernames():
                    handler.remove(username)


    def get_members(self):
        members = set()
        for role in self.get_roles():
            rolename = role['name']
            handler = self.get_role(rolename)
            members = members.union(handler.get_usernames())
        return members


    #########################################################################
    # User Interface
    #########################################################################
    def get_roles_namespace(self, username):
        namespace = []

        for role in self.get_roles():
            rolename = role['name']
            namespace.append({
                'name': rolename,
                'title': role['unit'],
                'selected': self.is_in_role(rolename, username)
            })

        return namespace


    permissions_form__access__ = 'is_admin'
    permissions_form__label__ = u"Permissions"
    permissions_form__sublabel__ = u"Permissions"
    def permissions_form(self, context):
        root = context.root
        userfolder = root.get_handler('users')
        namespace = {}

        members = self.get_members()

        users = []
        others = []
        # XXX This code is slow when there are many users, because the
        # method "userfolder.get_handler" is too expensive.
        get_user = userfolder.get_handler
        for name in userfolder.get_handler_names():
            if name[-9:] == '.metadata':
                continue
            user = get_user(name)
            if name in members:
                users.append({'name': name,
                              'title_or_name': user.get_title_or_name(),
                              'roles': self.get_roles_namespace(name)})
            else:
                others.append({'name': name,
                               'title_or_name': user.get_title_or_name()})

        users.sort(key=lambda x: x['title_or_name'])
        others.sort(key=lambda x: x['title_or_name'])

        namespace['users'] = users
        namespace['others'] = others

        handler = self.get_handler('/ui/Folder_permissions.xml')
        return stl(handler, namespace)


    permissions__access__ = 'is_admin'
    def permissions(self, context):
        # Permissions to remove
        if context.has_form_value('delete'):
            for username in context.get_form_values('delusers'):
                self.del_roles(username)
            return context.come_back(u"Members deleted.")

        # Permissions to add
        if context.has_form_value('add'):
            default_role = self.get_roles()[0]['name']
            for username in context.get_form_values('addusers'):
                self.set_role(default_role, username)
            return context.come_back(u"Members added.")

        # Permissions to change
        if context.has_form_value('update'):
            root = context.root
            userfolder = root.get_handler('users')
            for key in context.get_form_keys():
                if key in ['delusers', 'addusers', 'update', 'delete', 'add']:
                    continue
                new_role = context.get_form_value(key)
                self.set_role(new_role, key)

            return context.come_back(u"Roles updated.")
