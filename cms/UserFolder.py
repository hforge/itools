# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools import handlers
from itools.xml.stl import stl

# Import from ikaaro
from exceptions import UserError
from utils import comeback
from widgets import Table
from Folder import Folder
from Handler import Handler
from Metadata import Metadata
from User import User


class UserFolder(Folder):

    class_id = 'users'
    class_version = '20040625'
    class_icon16 = 'images/UserFolder16.png'
    class_icon48 = 'images/UserFolder48.png'


    def get_document_types(self):
        return [User]


    #######################################################################
    # Skeleton
    #######################################################################
    def get_skeleton(self, users=[]):
        skeleton = {}
        for username, password in users:
            user = User(password=password)
            skeleton[username] = user
            metadata = self.build_metadata(user, owner=username)
            skeleton['.%s.metadata' % username] = metadata
        return skeleton


    #######################################################################
    # API
    #######################################################################

    # XXX This method should not be defined, instead we should be able to
    # label the handlers that are multilingual.
    def _get_handler_names(self):
        return handlers.Folder.Folder._get_handler_names(self)


    def set_user(self, username, password):
        user = User(password=password)
        self.set_handler(username, user)


    def get_usernames(self):
        """
        Return all users name.
        """
        usernames = [ x for x in self.get_handler_names()
                      if not x.startswith('.') ]
        return frozenset(usernames)


    #######################################################################
    # Back-Office
    #######################################################################
    def get_views(self):
        return ['browse_thumbnails', 'new_user_form', 'edit_metadata_form']


    def get_subviews(self, view):
        if view in ['browse_thumbnails', 'browse_list']:
            return ['browse_thumbnails', 'browse_list']
        return []


    #######################################################################
    # Add
    new_user_form__access__ = Handler.is_admin
    new_user_form__label__ = u'Add'
    def new_user_form(self):
        root = self.get_root()

        tablename = 'groups_list'
        namespace = {}
        objects = []
        for path in root.get_groups():
            if path != '':
                group = root.get_handler(path)
                url = '%s/;%s' % (self.get_pathto(group),
                                  group.get_firstview())
                objects.append({'name': str(path), 'url': url})

        table = Table(self.get_pathtoroot(), tablename, objects,
                      sortby='name', sortorder='up',
                      batchstart='0', batchsize='0')
        namespace['table'] = table

        handler = self.get_handler('/ui/UserFolder_new_user.xml')
        return stl(handler, namespace)


    new_user__access__ = Handler.is_admin
    def new_user(self, username, password, password2, groups=[], **kw):
        # Check the values
        if not username:
            message = self.gettext(u'The username is wrong, please try again.')
            raise UserError, message
        if self.has_handler(username):
            message = (u'There is another user with the username "%s", '
                       u'please try again')
            raise UserError, self.gettext(message) % username
                  
        if not password or password != password2:
            message = self.gettext(u'The password is wrong, please try again.')
            raise UserError, message

        self.set_user(username, password)

        # Add user in groups
        root = self.get_root()
        for group_path in groups:
            group = root.get_handler(group_path)
            group.set_user(username)

        message = self.gettext(u'User added')
        comeback(message, goto='browse_thumbnails')


    def on_del_handler(self, segment):
        name = segment.name
        handler = self.get_handler(name)
        if isinstance(handler, User):
            root = self.get_root()
            for group_path in handler.get_groups():
                group = root.get_handler(group_path)
                group.remove_user(name)
        Folder.on_del_handler(self, segment)


Folder.register_handler_class(UserFolder)
