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
from itools import uri
from itools.datatypes import Email, Integer, Unicode
from itools.web import get_context
from itools.web.access import AccessControl as AccessControlBase
from itools.stl import stl
from itools.cms import widgets


class AccessControl(AccessControlBase):

    def is_admin(self, user, object=None):
        if user is None:
            return False
        root = get_context().root
        return root.has_user_role(user.name, 'ikaaro:admins')


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
        return self.has_user_role(user.name, *roles)


    def is_allowed_to_trans(self, user, object, name):
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user):
            return True

        # Reviewers can do everything
        username = user.name
        if self.has_user_role(username, 'ikaaro:reviewers'):
            return True

        # Members only can request and retract
        if self.has_user_role(username, 'ikaaro:members'):
            return name in ('request', 'unrequest')

        return False


    #########################################################################
    # API / Public
    #########################################################################
    def get_role_unit(self, name):
        for role in self.__roles__:
            if role['name'] == name:
                return self.gettext(role['unit'])
        return None


    def get_role_names(self):
        """
        Return the names of the roles available.
        """
        return [ r['name'] for r in self.__roles__ ]


    def get_user_role(self, user_id):
        """
        Return the role the user has here, or "None" if the user has not
        any role.
        """
        for role in self.get_role_names():
            value = self.get_property(role)
            if (value is not None) and (user_id in value):
                return role
        return None


    def has_user_role(self, user_id, *roles):
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


    def get_members_classified_by_role(self):
        roles = {}
        for rolename in self.get_role_names():
            usernames = self.get_property(rolename)
            roles[rolename] = set(usernames)
        return roles


    #########################################################################
    # User Interface
    #########################################################################
    def get_roles_namespace(self, username=None):
        # Build a list with the role name and unit
        namespace = [ {'name': x['name'], 'title': self.gettext(x['unit'])}
                      for x in self.__roles__ ]

        # If a username was not given, we are done
        if username is None:
            return namespace

        # Add the selected field
        user_role = self.get_user_role(username)
        for role in namespace:
            role['selected'] = (user_role == role['name'])

        return namespace


    #######################################################################
    # Browse
    permissions_form__access__ = 'is_authenticated'
    permissions_form__label__ = u"Members"
    permissions_form__sublabel__ = u"Browse Members"
    def permissions_form(self, context):
        namespace = {}

        # Get values from the request
        sortby = context.get_form_values('sortby', default=['email'])
        sortorder = context.get_form_value('sortorder', 'up')
        start = context.get_form_value('batchstart', default=0, type=Integer)
        size = 20

        # The search form
        field = context.get_form_value('search_field')
        term = context.get_form_value('search_term', type=Unicode)
        term = term.strip()

        search_fields = [('email', u'E-Mail'),
                         ('lastname', u'Last Name'),
                         ('firstname', u'First Name')]

        namespace['search_term'] = term
        namespace['search_fields'] = [
            {'id': name, 'title': self.gettext(title),
             'selected': name == field or None}
            for name, title in search_fields ]

        # Search
        catalog = self.get_handler('/.catalog')
        query = {'format': 'user'}
        if field:
            query[field] = term
        results = catalog.search(**query)

        roles = self.get_members_classified_by_role()

        # Build the namespace
        members = []
        for user in results.get_documents():
            user_id = user.name
            # Find out the user role. Skip the user if does not belong to
            # this group
            for role in roles:
                if user_id in roles[role]:
                    break
            else:
                continue
            # Build the namespace for the user
            ns = {}
            ns['checkbox'] = True
            ns['id'] = user_id
            ns['img'] = None
            # Email
            href = '/users/%s' % user_id
            ns['user_id'] = user_id, href
            # Title
            ns['email'] = user.email
            ns['firstname'] = user.firstname
            ns['lastname'] = user.lastname
            # Role
            role = self.get_role_unit(role)
            href = ';edit_membership_form?id=%s' % user_id
            ns['role'] = role, href
            # Append
            members.append(ns)

        # Sort
        members.sort(key=lambda x: x[sortby[0]])
        if sortorder == 'down':
            members.reverse()

        # Batch
        total = len(members)
        members = members[start:start+size]

        # The columns
        columns = [('user_id', u'User ID'),
                   ('email', u'E-Mail'),
                   ('firstname', u'First Name'),
                   ('lastname', u'Last Name'),
                   ('role', u'Role')]

        # The actions
        actions = [('permissions_del_members', self.gettext(u'Delete'),
                    'butto_delete', None)]

        namespace['batch'] = widgets.batch(context.uri, start, size, total)

        namespace['table'] = widgets.table(columns, members, sortby, sortorder,
                                           actions, self.gettext)

        handler = self.get_handler('/ui/RoleAware_permissions.xml')
        return stl(handler, namespace)


    permissions__access__ = 'is_admin'
    def permissions_del_members(self, context):
        usernames = context.get_form_values('delusers')
        self.set_user_role(usernames, None)

        # Reindex
        context.root.reindex_handler(self)

        # Back
        return context.come_back(u"Members deleted.")


    edit_membership_form__access__ = 'is_admin'
    def edit_membership_form(self, context):
        user_id = context.get_form_value('id')
        user = self.get_handler('/users/%s' % user_id)

        namespace = {}
        namespace['id'] = user_id
        namespace['name'] = user.get_property('dc:title')
        namespace['email'] = user.get_property('ikaaro:email')
        namespace['roles'] = self.get_roles_namespace(user_id)

        handler = self.get_handler('/ui/RoleAware_edit_membership_form.xml')
        return stl(handler, namespace)


    edit_membership__access__ = 'is_admin'
    def edit_membership(self, context):
        user_id = context.get_form_value('id')
        role = context.get_form_value('role')

        self.set_user_role(user_id, role)
        # Reindex
        context.root.reindex_handler(self)

        return context.come_back(u"Role updated.")


    #######################################################################
    # Add
    new_user_form__access__ = 'is_admin'
    new_user_form__label__ = u'Members'
    new_user_form__sublabel__ = u'New Member'
    def new_user_form(self, context):
        namespace = {}

        # Users (non-members)
        users = self.get_handler('/users')
        members = self.get_members()

        non_members = []
        for name in users.get_handler_names():
            # Work with the metadata
            if not name.endswith('.metadata'):
                continue
            # Check the user is not a member
            user_id = name[:-9]
            if user_id in members:
                continue
            # Add the user
            metadata = users.get_handler(name)
            email = metadata.get_property('ikaaro:email')
            non_members.append(email)

        non_members.sort()
        namespace['emails'] = non_members

        # Roles
        namespace['roles'] = self.get_roles_namespace()

        handler = self.get_handler('/ui/RoleAware_new_user.xml')
        return stl(handler, namespace)


    new_user__access__ = 'is_admin'
    def new_user(self, context):
        # Get the email
        email = context.get_form_value('email2')
        if not email:
            email = context.get_form_value('email')
            # Check the email is right
            if not email:
                message = u'The email address is missing, please type it.'
                return context.come_back(message)
            if not Email.is_valid(email):
                message = u'A valid email address must be provided.'
                return context.come_back(message)

        # Check wether the user exists
        root = context.root
        results = root.search(email=email)
        if results.get_n_documents():
            user_id = results.get_documents()[0].name
            # Check the user is not yet in the group
            members = self.get_members()
            if user_id in members:
                message = u'The user is already here.'
                return context.come_back(message)
        else:
            # A new user, add it
            password = context.get_form_value('password')
            password2 = context.get_form_value('password2')
            # Check the password is right
            if not password or password != password2:
                message = u'The password is wrong, please try again.'
                return context.come_back(message)
            # Add the user
            users = self.get_handler('/users')
            user = users.set_user(email, password)
            user_id = user.name

        # Set the role
        role = context.get_form_value('role')
        self.set_user_role(user_id, role)

        # Index the user
        root.reindex_handler(user)

        # Come back
        if context.has_form_value('add_and_return'):
            goto = None
        else:
            goto='/users/%s/;%s' % (user.name, user.get_firstview())
            goto = uri.get_reference(goto)

        return context.come_back(u'User added.', goto=goto)
