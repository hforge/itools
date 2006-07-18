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
import sha

# Import from itools
from itools import uri
from itools import i18n
from itools import handlers
from itools.stl import stl
from itools.web import get_context

# Import from ikaaro
from access import AccessControl
from widgets import Table
from Folder import Folder
from Handler import Handler
from metadata import Password
from registry import register_object_class



def crypt_password(password):
    return sha.new(password).digest()


class User(AccessControl, Folder):

    class_id = 'user'
    class_version = '20040625'
    class_title = 'User'
    class_icon16 = 'images/User16.png'
    class_icon48 = 'images/User48.png'
    class_views = [['profile'],
                   ['browse_thumbnails', 'browse_list', 'browse_image'],
                   ['new_resource_form'],
                   ['edit_form', 'edit_account_form', 'edit_groups_form'],
                   ['tasks_list']]


    ########################################################################
    # API
    ########################################################################
    def set_password(self, value):
        self.set_property('ikaaro:password', crypt_password(value))


    def authenticate(self, password):
        return password == self.get_property('ikaaro:password')


    def clear_group_cache(self):
        self._groups = None


    ########################################################################
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


    ########################################################################
    # Access control
    def is_allowed_to_edit(self, user, object):
        # You are nobody here, ha ha ha
        if user is None:
            return False

        # The all-powerfull
        if self.is_admin():
            return True

        # In my home I am the king (and only me)
        return self.name == user.name


    #######################################################################
    # User interface
    #######################################################################

    #######################################################################
    # Profile
    profile__access__ = 'is_allowed_to_view'
    profile__label__ = u'Profile'
    def profile(self, context):
        root = context.root
        user = context.user

        namespace = {}
        namespace['title'] = self.get_property('dc:title') or self.name
        # Owner
        is_owner = user is not None and user.name == self.name
        namespace['is_owner'] = is_owner
        # Owner or Admin
        is_admin = root.is_in_role('admins', user.name)
        namespace['is_owner_or_admin'] = is_owner or is_admin

        handler = self.get_handler('/ui/User_profile.xml')
        return stl(handler, namespace)


    #######################################################################
    # View
    view__access__ = 'is_allowed_to_view'
    view__label__ = u'View'
    def view(self, context):
        root = context.root

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


    #######################################################################
    # Edit
    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Preferences'
    edit_form__sublabel__ = u'Application'
    def edit_form(self, context):
        root = context.root
        user = context.user

        # Build the namespace
        namespace = {}

        # Languages
        languages = []
        user_language = self.get_property('ikaaro:user_language')
        for language_code in root.get_available_languages():
            languages.append({'code': language_code,
                              'name': i18n.get_language_name(language_code),
                              'is_selected': language_code == user_language})
        namespace['languages'] = languages

        handler = self.get_handler('/ui/User_edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        for key in ['ikaaro:user_language']:
            self.set_property(key, context.get_form_value(key))

        return context.come_back(u'Application preferences changed.')


    #######################################################################
    # Edit account
    edit_account_form__access__ = 'is_allowed_to_edit'
    edit_account_form__label__ = u'Preferences'
    edit_account_form__sublabel__ = u'Account'
    def edit_account_form(self, context):
        # Build the namespace
        namespace = {}
        namespace['fullname'] = self.get_property('dc:title')
        namespace['email'] = self.get_property('ikaaro:email')

        if self.name != context.user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/User_edit_account.xml')
        return stl(handler, namespace)


    edit_account__access__ = 'is_allowed_to_edit'
    def edit_account(self, context):
        title = context.get_form_value('dc:title')
        email = context.get_form_value('email')
        password = context.get_form_value('password')

        user = context.user
        if self.name == user.name:
            password = crypt_password(password)
            if not self.authenticate(password):
                return context.come_back(
                    u"You mistyped your actual password, your account is"
                    u" not changed.")

        self.set_property('dc:title', title, language='en')
        email = unicode(email, 'utf-8')
        self.set_property('ikaaro:email', email)
        message = self.gettext(u'Account changed.')
        comeback(message)


    #######################################################################
    # Edit password
    edit_password_form__access__ = 'is_self_or_superuser'
    edit_password_form__label__ = u'Preferences'
    edit_password_form__sublabel__ = u'Password'
    def edit_password_form(self):
        context = get_context()
        user = context.user

        # Build the namespace
        namespace = {}
        if self.name != user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/User_edit_password.xml')
        return stl(handler, namespace)


    edit_password__access__ = 'is_self_or_superuser'
    def edit_password(self, newpass, newpass2, password='', **kw):
        context = get_context()
        user = context.user

        if self.name == user.name:
            password = crypt_password(password)
            if not self.authenticate(password):
                message = (u"You mistyped your actual password, "
                           u"you account is not changed.")
                raise UserError, self.gettext(message)

        newpass = newpass.strip()
        if newpass:
            if newpass != newpass2:
                return context.come_back(
                    u"Passwords mismatch, please try again.")

            self.set_password(newpass)
            context = get_context()
            # Update the cookie if we updated our own password
            if self.name == user.name:
                # XXX This is a copy of the code in WebSite.login, should
                # refactor
                newpass = crypt_password(newpass)
                cookie = Password.encode('%s:%s' % (self.name, newpass))
                request = context.request
                expires = request.form.get('iAuthExpires', None)
                if expires is None:
                    context.set_cookie('__ac', cookie, path='/')
                else:
                    context.set_cookie('__ac', cookie, path='/',
                                       expires=expires)

        return context.come_back(u'Password changed.')


    #######################################################################
    # Edit user groups
    edit_groups_form__access__ = 'is_admin'
    edit_groups_form__label__ = u'Edit'
    edit_groups_form__sublabel__ = u'Groups'
    def edit_groups_form(self, context):
        root = context.root

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
    def edit_groups(self, context):
        groups = context.get_form_values('groups')
        # Add user in groups
        root = context.root
        all_groups = root.get_groups()
        for group_path in all_groups:
            group = root.get_handler(group_path)
            group.remove_users([self.name])
        for group_path in groups:
            group = root.get_handler(group_path)
            group.set_user(self.name)

        return context.come_back(u'User groups edited.')


    #######################################################################
    # Tasks
    tasks_list__access__ = 'is_allowed_to_edit'
    tasks_list__label__ = u'Tasks'
    def tasks_list(self, context):
        root = context.root

        namespace = {}
        documents = []
        for brain in root.search(workflow_state='pending'):
            document = root.get_handler(brain.abspath)
            if not document.is_allowed_to_view():
                continue
            documents.append({'url': '%s/;%s' % (self.get_pathto(document),
                                                 document.get_firstview()),
                             'title': document.title_or_name})
        namespace['documents'] = documents

        handler = self.get_handler('/ui/User_tasks.xml')
        return stl(handler, namespace)


register_object_class(User)



class UserFolder(Folder):

    class_id = 'users'
    class_version = '20040625'
    class_icon16 = 'images/UserFolder16.png'
    class_icon48 = 'images/UserFolder48.png'
    class_views = [['browse_thumbnails', 'browse_list'],
                   ['new_user_form'],
                   ['edit_metadata_form']]


    def get_document_types(self):
        return [User]


    #######################################################################
    # Skeleton
    #######################################################################
    def get_skeleton(self, users=[]):
        Folder.new(self)
        cache = self.cache
        for username, password in users:
            password = crypt_password(password)
            user = User()
            cache[username] = user
            metadata = {'owner': username, 'ikaaro:password': password}
            metadata = self.build_metadata(user, **metadata)
            cache['%s.metadata' % username] = metadata


    #######################################################################
    # API
    #######################################################################

    # XXX This method should not be defined, instead we should be able to
    # label the handlers that are multilingual.
    def _get_handler_names(self):
        return handlers.Folder.Folder._get_handler_names(self)


    def set_user(self, username, password):
        user = User()
        # Set the paswword
        password = crypt_password(password)
        self.set_handler(username, user, **{'ikaaro:password': password})
        return user


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

    #######################################################################
    # Add
    new_user_form__access__ = 'is_admin'
    new_user_form__label__ = u'Add'
    def new_user_form(self, context):
        root = context.root

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


    new_user__access__ = 'is_admin'
    def new_user(self, context):
        username = context.get_form_value('username')
        password = context.get_form_value('password')
        password2 = context.get_form_value('password2')
        groups = context.get_form_values('groups')

        # Check the values
        if not username:
            return context.come_back(
                u'The username is wrong, please try again.')
        if self.has_handler(username):
            return context.come_back(
                u'There is another user with the username "%s", please'
                u' try again')

        if not password or password != password2:
            return context.come_back(
                u'The password is wrong, please try again.')

        user = self.set_user(username, password)

        # Add user in groups
        root = context.root
        for group_path in groups:
            group = root.get_handler(group_path)
            group.set_user(username)

        if context.has_form_value('add_and_return'):
            goto = ';%s' % self.get_browse_view()
        else:
            goto='./%s/;%s' % (username, user.get_firstview())
        goto = uri.get_reference(goto)

        message = self.gettext(u'User added.')
        return goto.replace(message=message)


    def on_del_handler(self, segment):
        name = segment.name
        handler = self.get_handler(name)
        if isinstance(handler, User):
            root = self.get_root()
            for group_path in handler.get_groups():
                group = root.get_handler(group_path)
                group.remove_user(name)
        Folder.on_del_handler(self, segment)


register_object_class(UserFolder)
