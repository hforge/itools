# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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

# Import from the Standard Library
import sha

# Import from itools
from itools import uri
from itools import i18n
from itools import handlers
from itools.stl import stl

# Import from ikaaro
from access import AccessControl
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
                   ['edit_form', 'edit_account_form', 'edit_password_form'],
                   ['tasks_list']]


    ########################################################################
    # Indexing
    ########################################################################
    def get_catalog_indexes(self):
        indexes = Folder.get_catalog_indexes(self)
        indexes['email'] = self.get_property('ikaaro:email')
        indexes['username'] = self.get_property('ikaaro:username')
        return indexes


    ########################################################################
    # API
    ########################################################################
    def set_password(self, value):
        self.set_property('ikaaro:password', crypt_password(value))


    def authenticate(self, password):
        if self.get_property('ikaaro:user_must_confirm'):
            return False
        return password == self.get_property('ikaaro:password')


    def get_groups(self):
        """
        Returns all the role aware handlers where this user is a member.
        """
        root = self.get_root()
        if root is None:
            return ()

        catalog = root.get_handler('.catalog')
        results = catalog.search(is_role_aware=True, members=self.name)
        groups = [ x.abspath for x in results.get_documents() ]
        return tuple(groups)


    ########################################################################
    # Access control
    def is_self_or_admin(self, user, object):
        # You are nobody here, ha ha ha
        if user is None:
            return False

        # In my home I am the king
        if self.name == user.name:
            return True

        # The all-powerfull
        return self.is_admin(user)


    is_allowed_to_edit = is_self_or_admin


    #######################################################################
    # User interface
    #######################################################################

    #######################################################################
    # Registration
    confirm_registration__access__ = True
    def confirm_registration(self, context):
        must_confirm = self.get_property('ikaaro:user_must_confirm')
        if context.get_form_value('key') != must_confirm:
            return self.gettext(u"Bad key.").encode('utf-8')

        self.del_property('ikaaro:user_must_confirm')
        context.commit = True

        message = u'Registration confirmed, please log in'
        goto = '/;login_form?username=%s' % self.get_property('ikaaro:email')
        return context.come_back(message, goto=goto)


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
        namespace['is_owner_or_admin'] = is_owner or root.is_admin(user)

        handler = self.get_handler('/ui/User_profile.xml')
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
        self.set_property('ikaaro:email', email)

        # Reindex
        root = context.root
        root.reindex_handler(self)

        return context.come_back(u'Account changed.')


    #######################################################################
    # Edit password
    edit_password_form__access__ = 'is_allowed_to_edit'
    edit_password_form__label__ = u'Preferences'
    edit_password_form__sublabel__ = u'Password'
    def edit_password_form(self, context):
        user = context.user

        # Build the namespace
        namespace = {}
        if self.name != user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/User_edit_password.xml')
        return stl(handler, namespace)


    edit_password__access__ = 'is_allowed_to_edit'
    def edit_password(self, context):
        newpass = context.get_form_value('newpass')
        newpass2 = context.get_form_value('newpass2')
        password = context.get_form_value('password')
        user = context.user

        if self.name == user.name:
            password = crypt_password(password)
            if not self.authenticate(password):
                return context.come_back(u"You mistyped your actual password, "
                                         u"your account is not changed.")

        newpass = newpass.strip()
        if newpass:
            if newpass != newpass2:
                return context.come_back(
                    u"Passwords mismatch, please try again.")

            self.set_password(newpass)
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
    # Tasks
    tasks_list__access__ = 'is_allowed_to_edit'
    tasks_list__label__ = u'Tasks'
    def tasks_list(self, context):
        root = context.root
        user = context.user

        namespace = {}
        documents = []
        for brain in root.search(workflow_state='pending').get_documents():
            document = root.get_handler(brain.abspath)
            ac = document.get_access_control()
            if not ac.is_allowed_to_view(user, document):
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
    def new(self, users=[]):
        Folder.new(self)
        cache = self.cache
        for id, value in enumerate(users):
            id = str(id)
            email, password = value
            # Add User
            user = User()
            cache[id] = user
            # Add metadata
            metadata = {'owner': id, 'ikaaro:email': email,
                        'ikaaro:password': crypt_password(password)}
            cache['%s.metadata' % id] = self.build_metadata(user, **metadata)


    #######################################################################
    # API
    #######################################################################

    # XXX This method should not be defined, instead we should be able to
    # label the handlers that are multilingual.
    def _get_handler_names(self):
        return handlers.Folder.Folder._get_handler_names(self)


    def set_user(self, email, password):
        user = User()

        # Calculate the user id
        ids = []
        for key in self.cache:
            try:
                key = int(key)
            except ValueError:
                continue
            ids.append(key)
        if ids:
            ids.sort()
            user_id = str(ids[-1] + 1)
        else:
            user_id = '0'

        # Set the email and paswword
        password = crypt_password(password)
        self.set_handler(user_id, user, **{'ikaaro:email': email,
                                           'ikaaro:password': password,
                                           'dc:title': email})

        # Return the user
        return self.get_handler(user_id)


    def get_usernames(self):
        """
        Return all users name.
        """
        usernames = [ x for x in self.get_handler_names() 
                                 if not x.endswith('.metadata') ]
        return frozenset(usernames)


    #######################################################################
    # Back-Office
    #######################################################################

    rename_form__access__ = False
    rename__access__ = False
    cut__access__ = False


    #######################################################################
    # Add
    new_user_form__access__ = 'is_admin'
    new_user_form__label__ = u'Add'
    def new_user_form(self, context):
        handler = self.get_handler('/ui/UserFolder_new_user.xml')
        return stl(handler)


    new_user__access__ = 'is_admin'
    def new_user(self, context):
        email = context.get_form_value('email')
        password = context.get_form_value('password')
        password2 = context.get_form_value('password2')
        groups = context.get_form_values('groups')

        # Check the email is not empty
        if not email:
            return context.come_back(
                u'The email is wrong, please try again.')

        # Check there is not already a user with that email
        root = context.root
        catalog = root.get_handler('.catalog')
        results = catalog.search(email=email)
        if results.get_n_documents():
            message = (u'There is another user with the email "%s", '
                    u'please try again')
            return context.come_back(message % email)

        # Check the password is right
        if not password or password != password2:
            return context.come_back(
                u'The password is wrong, please try again.')

        # Add the user
        user = self.set_user(email, password)

        # Add user in groups
        for group_path in groups:
            group = root.get_handler(group_path)
            group.set_user(user.name)

        # Come back
        if context.has_form_value('add_and_return'):
            goto = ';%s' % self.get_browse_view()
        else:
            goto='./%s/;%s' % (user.name, user.get_firstview())
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
                group.set_user_role(name, None)
        Folder.on_del_handler(self, segment)


register_object_class(UserFolder)
