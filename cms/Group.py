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

# Import from the Standard Library
from time import time

# Import from itools
from itools import handlers
from itools.stl import stl
from itools.web import get_context
from itools.web.exceptions import UserError

# Import from ikaaro
from access import AccessControl
from utils import comeback, checkid
from widgets import Table
from Folder import Folder
from Handler import Handler



class ListOfUsers(handlers.File.File):

    def _load_state(self, resource):
        state = self.state

        state.usernames = set()
        for username in resource.readlines():
            username = username.strip()
            if username:
                state.usernames.add(username)


    def to_str(self):
        return '\n'.join(self.state.usernames)



class Group(Folder):

    class_id = 'group'
    class_version = '20040625'
    class_title = u'Group'
    class_icon16 = 'images/Group16.png'
    class_icon48 = 'images/Group48.png'


    #######################################################################
    # Skeleton
    #######################################################################
    def get_skeleton(self, users=[]):
        # Build the users handler manually, as a test (the other option is
        # to build a handler class just to manage '.users')
        data = '\n'.join(users)
        users = ListOfUsers()
        users.resource.write(data)

        return {'.users': users}


    #######################################################################
    # Catalog
    #######################################################################
    def get_catalog_indexes(self):
        document = Folder.get_catalog_indexes(self)
        document['is_group'] = True
        document['usernames'] = self.get_usernames()
        return document


    #######################################################################
    # API
    #######################################################################
    def _get_handler(self, segment, resource):
        name = segment.name
        if name == '.users':
            return ListOfUsers(resource)
        return Folder._get_handler(self, segment, resource)


    def set_user(self, username):
        username = username.strip()
        if username:
            list_of_users = self.get_handler('.users')
            list_of_users.set_changed()
            list_of_users.state.usernames.add(username)
            self.set_changed()


    def get_usernames(self):
        usernames = self.get_handler('.users').state.usernames

        # XXX This reliability check slows down too much
        user_folder = self.get_site_root().get_handler('users')
        return usernames & user_folder.get_usernames()


    def get_subgroups(self):
        """
        Returns a list with all the subgroups, including the subgroups of
        the subgroups, etc..
        """
        for handler in self.traverse():
            if isinstance(handler, Group):
                yield handler


    #######################################################################
    # User interface
    #######################################################################
    def get_views(self):
        return ['browse_users', 'browse_thumbnails', 'edit_metadata_form']


    def get_subviews(self, name):
        views = [['browse_users', 'add_users_form'],
                 ['browse_thumbnails', 'browse_list', 'add_group_form']]
        for subviews in views:
            if name in subviews:
                return subviews
        return Folder.get_subviews(self, name)


    is_allowed_to_view = AccessControl.is_admin
    

    #######################################################################
    # Groups
    browse_thumbnails__label__ = u'Groups'


    add_group_form__access__ = 'is_admin'
    add_group_form__label__ = u'Add'
    add_group_form__sublabel__ = u'Add'
    def add_group_form(self):
        handler = self.get_handler('/ui/Group_add_group.xml')
        return stl(handler)


    add_group__access__ = 'is_admin'
    def add_group(self, name, **kw):
        # Process input data
        name = name.strip()
        if not name:
            # Empty name
            raise UserError, self.gettext(u'The name must be entered')

        name = checkid(name)
        if name is None:
            # Invalid name
            message = (u'The name contains illegal characters, choose'
                       u' another one.')
            raise UserError, self.gettext(message)

        if self.has_handler(name):
            # Name already used
            message = u'There is already another group with this name.'
            raise UserError, self.gettext(message)

        self.set_handler(name, Group())

        message = self.gettext(u'Group added.')
        comeback(message, goto=';browse_thumbnails')


    #######################################################################
    # Users / Browse
    browse_users__access__ = 'is_admin'
    browse_users__label__ = u'Users'
    browse_users__sublabel__ = u'Browse'
    def browse_users(self):
        context = get_context()
        root = context.root

        namespace = {}
        tablename = 'users'

        # Get the objects
        context = get_context()
        path_to_root = self.get_pathto(root)
        objects = []
        for username in self.get_usernames():
            user = root.get_user(username)
            url = '%s/users/%s/;%s' % (path_to_root, username,
                                       user.get_firstview())
            objects.append({'name': username, 'fullname': user.title,
                            'url': url})

        # Use the widget
        table = Table(path_to_root, tablename, objects, sortby='name',
                      sortorder='up', batchstart='0', batchsize='0')

        # Add the total
        namespace['table'] = table
        namespace['total'] = len(objects)

        handler = self.get_handler('/ui/Group_browse_users.xml')
        return stl(handler, namespace)


    remove_users__access__ = 'is_admin'
    def remove_users(self, ids=[], **kw):
        context = get_context()
        request, response = context.request, context.response
        root = self.get_root()

        if not ids:
            message = self.gettext(u'You must select the members to remove.')
            raise UserError, message

        user_folder = root.get_handler('users')
        # Remove users in sub-groups
        for subgroup in self.get_subgroups():
            for name in ids:
                if name in subgroup.get_usernames():
                    subgroup.remove_user(name)

        # Remove from this group
        for name in ids:
            self.remove_user(name)
            # Empty group cache
            user = user_folder.get_handler(name)
            user.clear_group_cache()

        if len(ids) == 1:
            message = self.gettext(u'User removed.')
        else:
            message = self.gettext(u'Users removed.')
        comeback(message)


    def remove_user(self, username):
        list_of_users = self.get_handler('.users')

        username = username.strip()
        if username in list_of_users.state.usernames:
            list_of_users.set_changed()
            list_of_users.state.usernames.remove(username)
            self.set_changed() 


    #######################################################################
    # Users / Add
    add_users_form__access__ = 'is_admin'
    add_users_form__label__ = u'Users'
    add_users_form__sublabel__ = u'Add'
    def add_users_form(self):
        context = get_context()
        root = context.root

        # Users owned by my parent.
        parent = self.parent
        while not isinstance(parent, Group):
            parent = parent.parent
        pusernames = parent.get_usernames()
        usernames = pusernames.difference(self.get_usernames())
        usernames = list(usernames)
        usernames.sort()

        # Build the namespace
        namespace = {}
        namespace['users'] = [ {'name': x, 'title': x} for x in usernames ]
        namespace['nb_users'] = len(usernames) - 1
        if len(usernames)  > 10 :
             namespace['size'] = 10
        else:
             namespace['size'] = len(usernames)
        namespace['name'] = self.name
        namespace['parent'] = self.parent.name
        if (self.parent.name == 'groups') or (pusernames):
            namespace['parent'] = ''

        handler = self.get_handler('/ui/Group_add_users.xml')
        return stl(handler, namespace)


    add_users__access__ = 'is_admin'
    def add_users(self, names=[], **kw):
        """
        Form action that adds new members to the group.
        """
        userfolder = self.get_root().get_handler('users')
        for name in names:
            group_id = self.get_abspath().split('/')[3:]
            self.set_user(name)
            # Empty group cache
            user = userfolder.get_handler(name)
            user.clear_group_cache()

        if len(names) == 0:
             message = u'No user added'
        elif len(names) == 1: 
             message = u'User added'
        else:
             message = u'Users added'
        message = self.gettext(message)
        comeback(message, goto=';browse_users')


Folder.register_handler_class(Group)
