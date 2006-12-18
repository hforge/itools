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

# Import from itools
from itools.web import get_context
from itools.web.access import AccessControl as AccessControlBase
from itools.stl import stl


class AccessControl(AccessControlBase):

    def is_admin(self, user, object=None):
        if user is None:
            return False
        return get_context().root.has_role(user.name, 'ikaaro:admins')


    def is_allowed_to_view(self, user, object):
        # Objects with workflow
        from workflow import WorkflowAware
        if isinstance(object, WorkflowAware):
            state = object.workflow_state
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



class RoleAware(AccessControl):
    """
    This base class implements access control based on the concept of roles.
    Includes a user interface.
    """

    #########################################################################
    # To override
    #########################################################################
    __roles__ = [
        {'name': 'ikaaro:members', 'title': u"Members", 'unit': u"Member"},
        {'name': 'ikaaro:reviewers', 'title': u"Reviewers", 'unit': u"Reviewer"},
    ]


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
        username = user.name
        if (self.has_role(username, 'ikaaro:reviewers') or
                self.has_role(username, 'ikaaro:members')):
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
        username = user.name
        if self.has_role(username, 'ikaaro:reviewers'):
            return True

        # Members only can request and retract
        if self.has_role(username, 'ikaaro:members'):
            return name in ('request', 'unrequest')

        return False


    #########################################################################
    # API
    #########################################################################
    def get_role_names(self):
        return [r['name'] for r in self.__roles__]


    def has_role(self, username, rolename):
        return username in self.get_property(rolename)
  
  
    def del_roles(self, usernames):
        if isinstance(usernames, str):
            usernames = (usernames,)
        for rolename in self.get_role_names():
            current_users = self.get_property(rolename)
            current_users = tuple([x for x in current_users
                    if x not in usernames])
            self.set_property(rolename, current_users)
        get_context().root.reindex_handler(self)


    def set_role(self, new_role, usernames):
        if isinstance(usernames, str):
            usernames = (usernames,)
        for rolename in self.get_role_names():
            current_users = self.get_property(rolename)
            if new_role == rolename:
                current_users += tuple([x for x in usernames
                    if x not in current_users])
                self.set_property(rolename, current_users)
            else:
                current_users = tuple([x for x in current_users
                    if x not in usernames])
                self.set_property(rolename, current_users)
        get_context().root.reindex_handler(self)


    def get_members(self):
        members = set()
        for rolename in self.get_role_names():
            usernames = self.get_property(rolename)
            members = members.union(usernames)
        return members


    #########################################################################
    # User Interface
    #########################################################################
    def get_roles_namespace(self, username):
        namespace = []

        for role in self.__roles__:
            rolename = role['name']
            namespace.append({
                'name': rolename,
                'title': role['unit'],
                'selected': self.has_role(username, rolename),
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
            if name.endswith('.metadata'):
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
            usernames = context.get_form_values('delusers')
            self.del_roles(usernames)
            return context.come_back(u"Members deleted.")

        # Permissions to add
        if context.has_form_value('add'):
            default_role = self.get_role_names()[0]
            usernames = context.get_form_values('addusers')
            self.set_role(default_role, usernames)
            return context.come_back(u"Members added.")

        # Permissions to change
        if context.has_form_value('update'):
            new_roles = {}
            for key in context.get_form_keys():
                if key in ['delusers', 'addusers', 'update', 'delete', 'add']:
                    continue
                username = key
                new_role = context.get_form_value(username)
                new_roles.setdefault(new_role, []).append(username)
            for new_role, usernames in new_roles.items():
                self.set_role(new_role, usernames)
            return context.come_back(u"Roles updated.")
