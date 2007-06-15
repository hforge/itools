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
from itools.uri import get_reference
from itools.datatypes import Email, Integer, Unicode
from itools.web import get_context, AccessControl as AccessControlBase
from itools.stl import stl
from messages import *
from utils import generate_password
import widgets


class AccessControl(AccessControlBase):

    def is_admin(self, user, object):
        if user is None:
            return False
        # WebSite admin?
        root = object.get_site_root()
        if root.has_user_role(user.name, 'ikaaro:admins'):
            return True
        # Global admin?
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
        return self.is_admin(user, object)


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
        {'name': 'ikaaro:guests', 'title': u"Guest"},
        {'name': 'ikaaro:members', 'title': u"Member"},
        {'name': 'ikaaro:reviewers', 'title': u"Reviewer"},
    ]


    #########################################################################
    # Access Control
    #########################################################################
    def is_allowed_to_view(self, user, object):
        # Get the variables to resolve the formula
        # Intranet or Extranet
        is_open = self.get_property('ikaaro:website_is_open')
        # The role of the user
        if user is None:
            role = None
        elif self.is_admin(user, object):
            role = 'ikaaro:admins'
        else:
            role = self.get_user_role(user.name)
        # The state of the object
        from workflow import WorkflowAware
        if isinstance(object, WorkflowAware):
            state = object.workflow_state
        else:
            state = 'public'

        # The formula
        # Extranet
        if is_open:
            if state == 'public':
                return True
            return role is not None
        # Intranet
        if role in ('ikaaro:admins', 'ikaaro:reviewers', 'ikaaro:members'):
            return True
        elif role == 'ikaaro:guests':
            return state == 'public'
        return False


    def is_allowed_to_edit(self, user, object):
        from workflow import WorkflowAware
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user, object):
            return True

        # Reviewers too
        if self.has_user_role(user.name, 'ikaaro:reviewers'):
            return True

        # Members only can touch not-yet-published documents
        if self.has_user_role(user.name, 'ikaaro:members'):
            if isinstance(object, WorkflowAware):
                state = object.workflow_state
                # Anybody can see public objects
                if state != 'public':
                    return True

        return False


    def is_allowed_to_add(self, user, object):
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user, object):
            return True

        # Reviewers too
        return self.has_user_role(user.name, 'ikaaro:reviewers',
                                  'ikaaro:members')


    def is_allowed_to_trans(self, user, object, name):
        # Anonymous can touch nothing
        if user is None:
            return False

        # Admins are all powerfull
        if self.is_admin(user, object):
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
    def get_role_title(self, name):
        for role in self.__roles__:
            if role['name'] == name:
                return self.gettext(role['title'])
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
        elif isinstance(user_ids, unicode):
            user_ids = [str(user_ids)]

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
        # Build a list with the role name and title
        namespace = [ {'name': x['name'], 'title': self.gettext(x['title'])}
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
        query = {'format': 'user'}
        if field:
            query[field] = term
        root = context.root
        results = root.search(**query)

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
            role = self.get_role_title(role)
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
                    'button_delete', None)]
        user = context.user
        ac = self.get_access_control()
        actions = [
            x for x in actions if ac.is_access_allowed(user, self, x[0]) ]

        namespace['batch'] = widgets.batch(context.uri, start, size, total)

        namespace['table'] = widgets.table(columns, members, sortby, sortorder,
                                           actions, self.gettext)

        handler = self.get_handler('/ui/access/permissions.xml')
        return stl(handler, namespace)


    permissions_del_members__access__ = 'is_admin'
    def permissions_del_members(self, context):
        usernames = context.get_form_values('ids')
        self.set_user_role(usernames, None)

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

        handler = self.get_handler('/ui/access/edit_membership_form.xml')
        return stl(handler, namespace)


    edit_membership__access__ = 'is_admin'
    def edit_membership(self, context):
        user_id = context.get_form_value('id')
        role = context.get_form_value('role')

        self.set_user_role(user_id, role)

        return context.come_back(u"Role updated.")


    #######################################################################
    # Add
    new_user_form__access__ = 'is_admin'
    new_user_form__label__ = u'Members'
    new_user_form__sublabel__ = u'New Member'
    def new_user_form(self, context):
        namespace = {}

        # Admin can set the password directly
        namespace['is_admin'] = self.is_admin(context.user, self)

        # Roles
        namespace['roles'] = self.get_roles_namespace()

        handler = self.get_handler('/ui/access/new_user.xml')
        return stl(handler, namespace)


    new_user__access__ = 'is_admin'
    def new_user(self, context):
        root = context.root
        user = context.user
        users = root.get_handler('users')

        email = context.get_form_value('email')
        # Check the email is right
        if not email:
            message = u'The email address is missing, please type it.'
            return context.come_back(message)
        if not Email.is_valid(email):
            return context.come_back(MSG_INVALID_EMAIL)

        # Check whether the user already exists
        results = root.search(email=email)
        if results.get_n_documents():
            user_id = results.get_documents()[0].name
        else:
            user_id = None
 
        # Get the user (create it if needed)
        if user_id is None:
            # New user
            is_admin = self.is_admin(user, self)
            if is_admin:
                password = context.get_form_value('newpass')
                password2 = context.get_form_value('newpass2')
                # Check the password is right
                if password != password2:
                    return context.come_back(MSG_PASSWORD_MISMATCH)
                if not password:
                    # Admin can set no password
                    # so the user must activate its account
                    password = None
            else:
                password = None
            # Add the user
            user = users.set_user(email, password)
            user_id = user.name
            if password is None:
                key = generate_password(30)
                user.set_property('ikaaro:user_must_confirm', key)
                # Send confirmation email to activate the account
                user.send_confirmation(context, email)
        else:
            user = users.get_handler(user_id)
            # Check the user is not yet in the group
            members = self.get_members()
            if user_id in members:
                message = u'The user is already here.'
                return context.come_back(message)

        # Set the role
        role = context.get_form_value('role')
        self.set_user_role(user_id, role)

        # Come back
        if context.has_form_value('add_and_return'):
            goto = None
        else:
            goto='/users/%s/;%s' % (user.name, user.get_firstview())
            goto = get_reference(goto)

        return context.come_back(u'User added.', goto=goto)
