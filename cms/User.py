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
import base64
import sha
import urllib

# Import from itools
from itools import uri
from itools import i18n
from itools.handlers.KeyValue import KeyValue
from itools.xml.stl import stl
from itools.web import get_context
from itools.web.exceptions import UserError

# Import from ikaaro
from access import AccessControl
from utils import comeback
from widgets import Table
from Folder import Folder
from Handler import Handler



class UserData(KeyValue):

    __keys__ = ['password', 'email']
    __keys_types__ = {'email': 'unicode'}


    def get_skeleton(self, password=None):
        # Encode with a digest method
        password = sha.new(password).digest()
        # Transform to an ascci string
        password = base64.encodestring(password)
        # Quote the newlines
        password = urllib.quote(password)
        return 'password:%s\n' % password



class User(Folder):

    class_id = 'user'
    class_version = '20040625'
    class_title = 'User'
    class_icon16 = 'images/User16.png'
    class_icon48 = 'images/User48.png'


    #########################################################################
    # The skeleton
    #########################################################################
    def get_skeleton(self, password=None):
        user_data = UserData(password=password)
        return {'.data': user_data}


    def _get_handler(self, segment, resource):
        name = segment.name
        if name == '.data':
            return UserData(resource)
        return Folder._get_handler(self, segment, resource)


    #########################################################################
    # API
    #########################################################################
    def get_password(self):
        user_data = self.get_handler('.data')
        return user_data.state.password


    def set_password(self, value):
        user_data = self.get_handler('.data')
        user_data.set_changed()
        user_data.state.password = value            


    def get_email(self):
        user_data = self.get_handler('.data')
        return user_data.state.email


    def set_email(self, value):
        user_data = self.get_handler('.data')
        user_data.set_changed()
        user_data.state.email = value


    def authenticate(self, password):
        # Encode with a digest method
        password = sha.new(password).digest()
        # Load the users password (unquote and decode)
        # XXX Should be done when loading the handler
        self_password = self.get_password()
        self_password = base64.decodestring(urllib.unquote(self_password))
        # Transform to an ascci string
        return password == self_password


    #########################################################################
    # Groups
    _groups = None
    def get_groups(self):
        if self._groups is None:
            # Load groups
            root = self.get_root()
            if root is not None:
                catalog = root.get_handler('.catalog')
                brains = catalog.search(is_group=True, usernames=self.name)
                groups = [ x.abspath for x in brains ]
                self._groups = tuple(groups)

        return self._groups

    groups = property(get_groups, None, None, "")


    #########################################################################
    # Access control
    is_allowed_to_remove = AccessControl.is_admin
    is_allowed_to_move = AccessControl.is_admin
    is_allowed_to_copy = AccessControl.is_admin


    #######################################################################
    # User interface
    #######################################################################
    def get_views(self):
        views = ['welcome', 'browse_thumbnails', 'new_resource_form',
                 'edit_form']
        # Task list only for reviewers and admins (for now).
        root = get_context().root
        is_admin = self.name in root.get_handler('admins').get_usernames()
        is_rev = self.name in root.get_handler('reviewers').get_usernames()
        if is_admin or is_rev:
            views.append('tasks_list')

        return views


    def get_subviews(self, name):
        # The edit menu
        subviews = ['edit_form', 'edit_password_form', 'edit_groups_form']
        if name in subviews:
            return subviews
        return Folder.get_subviews(self, name)


    def clear_group_cache(self):
        self._groups = None


    #######################################################################
    # Welcome
    welcome__access__ = 'is_allowed_to_view'
    welcome__label__ = u'Welcome'
    def welcome(self):
        namespace = {}
        namespace['title'] = self.get_property('dc:title') or self.name
        # Tasks? (for now).
        root = get_context().root
        is_admin = self.name in root.get_handler('admins').get_usernames()
        is_rev = self.name in root.get_handler('reviewers').get_usernames()
        namespace['tasks'] = is_admin or is_rev

        handler = self.get_handler('/ui/User_welcome.xml')
        return stl(handler, namespace)


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self):
        root = self.get_root()

        namespace = {}
        namespace['label'] = self.title_or_name
        groups = []
        for group_path in self.get_groups():
            group = root.get_handler(group_path)
            path_to_group = self.get_pathto(group)

            group_ns = {}
            path_to_icon = group.get_path_to_icon(48)
            path_to_icon = uri.Path(str(path_to_group) + '/').resolve(path_to_icon)
            group_ns['logo'] = path_to_icon
            group_ns['url'] = '%s/;%s' % (path_to_group, group.get_firstview())
            group_ns['name'] = group.title_or_name 
            groups.append(group_ns)
        namespace['groups'] = groups

        handler = self.get_handler('/ui/User_view.xml')
        return stl(handler, namespace)


    def is_self_or_superuser(self):
        context = get_context()
        user = context.user

        if user is not None:
            # Is self?
            if user.name == self.name:
                return True
            # Is superuser?
            root = context.root
            admins = root.get_handler('admins')
            if user.name in admins.get_usernames():
                return True

        return False


    #######################################################################
    # Edit
    edit_form__access__ = 'is_self_or_superuser'
    edit_form__label__ = u'Preferences'
    edit_form__sublabel__ = u'Personal'
    def edit_form(self):
        context = get_context()
        root = context.root
        user = context.user

        # Build the namespace
        namespace = {}
        namespace['fullname'] = self.get_property('dc:title')
        namespace['email'] = self.get_email()

        # Languages
        languages = []
        user_language = self.get_property('ikaaro:user_language')
        for language_code in root.get_available_languages():
            languages.append({'code': language_code,
                              'name': i18n.get_language_name(language_code),
                              'is_selected': language_code == user_language})
        namespace['languages'] = languages

        # Themes
        themes = []
        user_theme = self.get_property('ikaaro:user_theme')
        for theme in root.get_themes():
            themes.append({'value': theme, 'is_selected': theme == user_theme})
        namespace['themes'] = themes

        if self.is_admin() and self.name != user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/User_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_self_or_superuser'
    def edit(self, email, **kw):
        context = get_context()
        user = context.user

        if not self.is_admin() or self.name == user.name:
            if not self.authenticate(kw['confirm']):
                message = u"You mistyped your password, \
                    your preferences were not changed."
                raise UserError, self.gettext(message)

        self.set_property('dc:title', kw['dc:title'], language='en')
        email = unicode(email, 'utf-8')
        self.set_email(email)
        self.set_property('ikaaro:user_theme', kw['ikaaro:user_theme'])
        self.set_property('ikaaro:user_language', kw['ikaaro:user_language'])

        message = self.gettext(u'User data changed.')
        comeback(message)


    #######################################################################
    # Edit / Password
    edit_password_form__access__ = 'is_self_or_superuser'
    edit_password_form__label__ = u'Preferences'
    edit_password_form__sublabel__ = u'Password'
    def edit_password_form(self):
        context = get_context()
        user = context.user

        namespace = {}
        if self.is_admin() or self.name != user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/User_edit_password.xml')
        return stl(handler, namespace)


    edit_password__access__ = 'is_self_or_superuser'
    def edit_password(self, password, password2, **kw):
        context = get_context()
        user = context.user

        if not self.is_admin() or user.name != self.name:
            if not self.authenticate(kw['confirm']):
                message = u"You mistyped your actual password, \
                    it will not be changed for the new password."
                raise UserError, self.gettext(message)

        if not password or password != password2:
            message = u"The password is wrong, please try again."
            raise UserError, self.gettext(message)

        self.set_password(base64.encodestring(sha.new(password).digest()))
        # Update the cookie if we updated our own password
        context = get_context()
        if self.name == context.user.name:
            request = context.request
            # XXX This is a copy of the code in WebSite.login, should refactor
            cname = '__ac'
            cookie = base64.encodestring('%s:%s' % (self.name, password))
            cookie = urllib.quote(cookie)
            expires = request.form.get('iAuthExpires', None)
            if expires is None:
                context.set_cookie(cname, cookie)
            else:
                context.set_cookie(cname, cookie, expires=expires)

        message = self.gettext(u'Password changed.')
        comeback(message)


    #######################################################################
    # Edit user groups
    edit_groups_form__access__ = 'is_admin'
    edit_groups_form__label__ = u'Edit'
    edit_groups_form__sublabel__ = u'Groups'
    def edit_groups_form(self):
        root = self.get_root()

        tablename = 'groups_list'
        namespace = {}
        objects = []
        for path in root.get_groups():
            if path != '':
                group = root.get_handler(path)
                url = '%s/;%s' % (self.get_pathto(group),
                                  group.get_firstview())
                checked = self.name in group.get_usernames()
                objects.append({'name': str(path), 'url': url,
                                'checked': checked})

        table = Table(self.get_pathtoroot(), tablename, objects,
                      sortby='name', sortorder='up',
                      batchstart='0', batchsize='0')
        namespace['table'] = table
        namespace['fullname'] = self.title

        handler = self.get_handler('/ui/User_edit_groups.xml')
        return stl(handler, namespace)


    edit_groups__access__ = 'is_admin'
    def edit_groups(self, groups=[], **kw):
        # Add user in groups
        root = self.get_root()
        all_groups = root.get_groups()
        for group_path in all_groups:
            group = root.get_handler(group_path)
            group.remove_users([self.name])
        for group_path in groups:
            group = root.get_handler(group_path)
            group.set_user(self.name)

        message = self.gettext(u'User groups edited')
        comeback(message)


    #######################################################################
    # Tasks
    tasks_list__access__ = 'is_self_or_superuser'
    tasks_list__label__ = u'Tasks'
    def tasks_list(self):
        context = get_context()
        root = context.root

        namespace = {}
        documents = []
        for brain in root.search(workflow_state='pending'):
            document = root.get_handler(brain.abspath)
            documents.append({'url': '%s/;%s' % (self.get_pathto(document),
                                                 document.get_firstview()),
                             'title': document.title_or_name})
        namespace['documents'] = documents

        handler = self.get_handler('/ui/User_tasks.xml')
        return stl(handler, namespace)


Folder.register_handler_class(User)
