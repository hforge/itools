# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.stl import stl
from itools.web.exceptions import UserError
from itools.web import get_context

# Import from ikaaro
from handlers import ListOfUsers
from utils import comeback



##class Group(Folder):

##    class_id = 'group'
##    class_version = '20040625'
##    class_title = u'Group'


##    #######################################################################
##    # Skeleton
##    #######################################################################
##    def get_skeleton(self, users=[]):
##        # Build the users handler manually, as a test (the other option is
##        # to build a handler class just to manage '.users')
##        return {'.users': ListOfUsers(users=users)}


##    #######################################################################
##    # Catalog
##    #######################################################################
##    def get_catalog_indexes(self):
##        document = Folder.get_catalog_indexes(self)
##        document['is_group'] = True
##        document['usernames'] = self.get_usernames()
##        return document



class RoleAware(object):

    __roles__ = [
        {'name': 'members', 'title': u"Members", 'unit': u"Member"},
        {'name': 'reviewers', 'title': u"Reviewers", 'unit': u"Reviewer"},
    ]


    def get_role(self, name):
        return self.get_handler('.%s.users' % name)


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
            skeleton['.%s.users' % rolename] = ListOfUsers(users=users)

        return skeleton


    def is_in_role(self, rolename, username=None):
        if username is None:
            context = get_context()
            user = context.user
            if user is None:
                return False
            username = user.name

        role = self.get_role(rolename)
        return username in role.get_usernames()


    def del_roles(self, username):
        for role in self.get_roles():
            handler = self.get_role(role['name'])
            if username in handler.get_usernames():
                handler.remove(username)

        context = get_context()
        root = context.root
        user = root.get_user(username)
        user.clear_group_cache()


    def set_role(self, rolename, username):
        for role in self.get_roles():
            handler = self.get_role(role['name'])
            if rolename == role['name']:
                if not username in handler.get_usernames():
                    handler.add(username)
            else:
                if username in handler.get_usernames():
                    handler.remove(username)

        context = get_context()
        root = context.root
        user = root.get_user(username)
        user.clear_group_cache()


    #########################################################################
    # User Interface
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


    def get_views(self):
        return ['permissions_form']


    def _get_members_sort_key(self):
        return 'title_or_name'


    permissions_form__access__ = 'is_allowed_to_edit'
    permissions_form__label__ = u"Permissions"
    def permissions_form(self, context):
        root = context.root
        userfolder = root.get_object('users')
        namespace = {}

        members = set()
        for role in self.get_roles():
            rolename = role['name']
            handler = self.get_role(rolename)
            members = members.union(handler.get_usernames())

        users = [userfolder.get_object(u) for u in members]
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

            message = u"Members deleted."
            return comeback(message)

        # permissions to add
        elif kw.get('add'):
            if isinstance(addusers, str):
                addusers = [addusers]
            for username in addusers:
                self.set_role('members', username)

            message = u"Members added."
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

            message = u"Roles updated."
            return comeback(message)
