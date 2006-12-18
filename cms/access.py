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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.web import get_context
from itools.web.access import AccessControl as AccessControlBase
from itools.stl import stl


class AccessControl(AccessControlBase):

    def is_admin(self, user, object=None):
        if user is None:
            return False
        root = get_context().root
        return root.user_has_role(user.name, 'ikaaro:admins')


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
        {'name': 'ikaaro:reviewers', 'title': u"Reviewers",
         'unit': u"Reviewer"},
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
        roles = 'ikaaro:reviewers', 'ikaaro:members'
        return self.user_has_role(user.name, *roles)


    def is_allowed_to_trans(self, user, object, name):
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user):
            return True

        # Reviewers can do everything
        username = user.name
        if self.user_has_role(username, 'ikaaro:reviewers'):
            return True

        # Members only can request and retract
        if self.user_has_role(username, 'ikaaro:members'):
            return name in ('request', 'unrequest')

        return False


    #########################################################################
    # API / Public
    #########################################################################
    def get_role_names(self):
        """
        Return the names of the roles available.
        """
        return [r['name'] for r in self.__roles__]


    def get_user_role(self, user_id):
        """
        Return the role the user has here, or "None" if the user has not
        any role.
        """
        for role in self.get_role_names():
            if user_id in self.get_property(role):
                return role
        return None


    def user_has_role(self, user_id, *roles):
        """
        Return True if the given user has any of the the given roles,
        False otherwise.
        """
        for role in roles:
            if user_id in self.get_property(role):
                return True
        return False
 

    def set_user_role(self, user_ids, role):
        """
        Sets the role for the given users. If "role" is None, removes the
        role of the users.
        """
        # The input parameter "user_ids" should be a list
        if isinstance(user_ids, str):
            user_ids = [user_ids]

        # Change "user_ids" to a set, to simplify the rest of the code
        user_ids = set(user_ids)

        # Build the list of roles from where the users will be removed
        roles = self.get_role_names()
        if role is not None:
            roles.remove(role)

        # Add the users to the given role
        if role is not None:
            users = self.get_property(role)
            users = set(users)
            if user_ids - users:
                users = tuple(users | user_ids)
                self.set_property(role, users)

        # Remove the user from the other roles
        for role in roles:
            users = self.get_property(role)
            users = set(users)
            if users & user_ids:
                users = tuple(users - user_ids)
                self.set_property(role, users)


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

        user_role = self.get_user_role(username)
        for role in self.__roles__:
            rolename = role['name']
            namespace.append({'name': rolename,
                              'title': role['unit'],
                              'selected': user_role == rolename})

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


    permissions_update_members__access__ = 'is_admin'
    def permissions_update_members(self, context):
        # Get the list of users to update
        root = context.root
        users = root.get_handler('users')
        usernames = users.get_usernames()
        form_keys = context.get_form_keys()
        usernames = set(usernames) & set(form_keys)

        # Update the user roles
        for username in usernames:
            role = context.get_form_value(username)
            self.set_user_role(username, role)

        # Reindex
        context.root.reindex_handler(self)

        # Back
        return context.come_back(u"Roles updated.")


    permissions__access__ = 'is_admin'
    def permissions_del_members(self, context):
        usernames = context.get_form_values('delusers')
        self.set_user_role(usernames, None)

        # Reindex
        context.root.reindex_handler(self)

        # Back
        return context.come_back(u"Members deleted.")

    
    permissions_add_members__access__ = 'is_admin'
    def permissions_add_members(self, context):
        usernames = context.get_form_values('addusers')

        default_role = self.get_role_names()[0]
        self.set_user_role(usernames, default_role)

        # Reindex
        context.root.reindex_handler(self)

        # Back
        return context.come_back(u"Members added.")
