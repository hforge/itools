# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2006 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from the Standard Library
import sha
from copy import deepcopy
from string import Template

# Import from itools
from itools.uri import Path
from itools.catalog import EqQuery, AndQuery, OrQuery
from itools.i18n import get_language_name
from itools.handlers import Folder as BaseFolder
from itools.stl import stl
from itools.datatypes import Email

# Import from ikaaro
from access import AccessControl
from folder import Folder
from metadata import Password
from messages import *
from registry import register_object_class, get_object_class


def crypt_password(password):
    return sha.new(password).digest()


class User(AccessControl, Folder):

    class_id = 'user'
    class_title = 'User'
    class_icon16 = 'images/User16.png'
    class_icon48 = 'images/User48.png'
    class_views = [
        ['profile'],
        ['browse_content?mode=thumbnails',
         'browse_content?mode=list',
         'browse_content?mode=image'],
        ['new_resource_form'],
        ['edit_account_form', 'edit_form', 'edit_password_form'],
        ['tasks_list']]


    ########################################################################
    # Indexing
    ########################################################################
    def get_catalog_indexes(self):
        indexes = Folder.get_catalog_indexes(self)
        indexes['email'] = self.get_property('ikaaro:email')
        indexes['username'] = self.get_login_name()
        return indexes


    ########################################################################
    # API
    ########################################################################
    def get_title(self):
        firstname = self.get_property('ikaaro:firstname')
        lastname = self.get_property('ikaaro:lastname')
        if firstname:
            if lastname:
                return '%s %s' % (firstname, lastname)
            return firstname
        if lastname:
            return lastname
        return self.get_login_name()


    def get_login_name(self):
        # FIXME Check first the username (for compatibility with 0.14)
        username = self.get_property('ikaaro:username')
        if username:
            return username
        return self.get_property('ikaaro:email')


    def set_password(self, password):
        crypted = crypt_password(password)
        self.set_property('ikaaro:password', crypted)


    def authenticate(self, password):
        if self.get_property('ikaaro:user_must_confirm'):
            return False
        # Is password crypted?
        if password == self.get_property('ikaaro:password'):
            return True
        # Is password clear?
        crypted = crypt_password(password)
        return crypted == self.get_property('ikaaro:password')


    def get_groups(self):
        """
        Returns all the role aware handlers where this user is a member.
        """
        root = self.get_root()
        if root is None:
            return ()

        results = root.search(is_role_aware=True, members=self.name)
        groups = [ x.abspath for x in results.get_documents() ]
        return tuple(groups)


    def set_auth_cookie(self, context, password):
        username = str(self.name)
        crypted = crypt_password(password)
        cookie = Password.encode('%s:%s' % (username, crypted))
        request = context.request
        expires = request.form.get('iAuthExpires', None)
        if expires is None:
            context.set_cookie('__ac', cookie, path='/')
        else:
            context.set_cookie('__ac', cookie, path='/', expires=expires)


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
        return self.is_admin(user, object)


    is_allowed_to_edit = is_self_or_admin


    #######################################################################
    # User interface
    #######################################################################

    #######################################################################
    # Registration
    def send_confirmation(self, context, email):
        hostname = context.uri.authority.host
        subject = u"[%s] Register confirmation required" % hostname
        subject = self.gettext(subject)
        body = self.gettext(u"To confirm your registration click the link:\n"
                            u"\n"
                            u"  $confirm_url")
        confirm_url = deepcopy(context.uri)
        path = '/users/%s/;confirm_registration_form' % self.name
        confirm_url.path = Path(path)
        key = self.get_property('ikaaro:user_must_confirm')
        confirm_url.query = {'key': key}
        body = Template(body).substitute({'confirm_url': str(confirm_url)})
        root = context.root
        root.send_email(root.contact_email, email, subject, body)


    confirm_registration_form__access__ = True
    def confirm_registration_form(self, context):
        # Check register key
        must_confirm = self.get_property('ikaaro:user_must_confirm')
        if (must_confirm is None
                or context.get_form_value('key') != must_confirm):
            return self.gettext(u"Bad key.").encode('utf-8')

        namespace = {'key': must_confirm}

        handler = self.get_handler('/ui/user/confirm_registration.xml')
        return stl(handler, namespace)


    confirm_registration__access__ = True
    def confirm_registration(self, context):
        keep = ['key']
        register_fields = [('newpass', True),
                           ('newpass2', True)]

        # Check register key
        must_confirm = self.get_property('ikaaro:user_must_confirm')
        if context.get_form_value('key') != must_confirm:
            return self.gettext(u"Bad key.").encode('utf-8')

        # Check input data
        error = context.check_form_input(register_fields)
        if error is not None:
            return context.come_back(error, keep=keep)

        # Check passwords
        password = context.get_form_value('newpass')
        password2 = context.get_form_value('newpass2')
        if password != password2:
            return context.come_back(MSG_PASSWORD_MISMATCH, keep=keep)

        # Set user
        self.set_password(password)
        self.del_property('ikaaro:user_must_confirm')

        # Set cookie
        self.set_auth_cookie(context, password)

        message = u'Registration confirmed, welcome.'
        goto = "./;%s" % self.get_firstview()
        return context.come_back(message, goto=goto)


    #######################################################################
    # Profile
    profile__access__ = 'is_allowed_to_view'
    profile__label__ = u'Profile'
    def profile(self, context):
        root = context.root
        user = context.user

        namespace = {}
        namespace['title'] = self.get_title_or_name()
        # Owner
        is_owner = user is not None and user.name == self.name
        namespace['is_owner'] = is_owner
        # Owner or Admin
        namespace['is_owner_or_admin'] = is_owner or root.is_admin(user, self)

        handler = self.get_handler('/ui/user/profile.xml')
        return stl(handler, namespace)


    #######################################################################
    # Edit
    edit_form__access__ = 'is_allowed_to_edit'
    edit_form__label__ = u'Edit'
    edit_form__sublabel__ = u'Preferences'
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
                              'name': get_language_name(language_code),
                              'is_selected': language_code == user_language})
        namespace['languages'] = languages

        handler = self.get_handler('/ui/user/edit.xml')
        return stl(handler, namespace)


    edit__access__ = 'is_allowed_to_edit'
    def edit(self, context):
        for key in ['ikaaro:user_language']:
            self.set_property(key, context.get_form_value(key))

        return context.come_back(u'Application preferences changed.')


    #######################################################################
    # Edit account
    account_fields = ['ikaaro:firstname', 'ikaaro:lastname', 'ikaaro:email']

    edit_account_form__access__ = 'is_allowed_to_edit'
    edit_account_form__label__ = u'Edit'
    edit_account_form__sublabel__ = u'Account'
    def edit_account_form(self, context):
        # Build the namespace
        namespace = {}
        for key in self.account_fields:
            namespace[key] = self.get_property(key)
        # Ask for password to confirm the changes
        if self.name != context.user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/user/edit_account.xml')
        return stl(handler, namespace)


    edit_account__access__ = 'is_allowed_to_edit'
    def edit_account(self, context):
        # Check password to confirm changes
        password = context.get_form_value('password')
        user = context.user
        if self.name == user.name:
            if not self.authenticate(password):
                return context.come_back(
                    u"You mistyped your actual password, your account is"
                    u" not changed.")

        # Check the email is good
        email = context.get_form_value('ikaaro:email')
        if not Email.is_valid(email):
            return context.come_back(MSG_INVALID_EMAIL)

        root = context.root
        results = root.search(email=email)
        if results.get_n_documents():
            message = (u'There is another user with the email "%s", '
                       u'please try again')

        # Save changes
        for key in self.account_fields:
            value = context.get_form_value(key)
            self.set_property(key, value)

        return context.come_back(u'Account changed.')


    #######################################################################
    # Edit password
    edit_password_form__access__ = 'is_allowed_to_edit'
    edit_password_form__label__ = u'Edit'
    edit_password_form__sublabel__ = u'Password'
    def edit_password_form(self, context):
        user = context.user

        # Build the namespace
        namespace = {}
        if self.name != user.name:
            namespace['must_confirm'] = False
        else:
            namespace['must_confirm'] = True

        handler = self.get_handler('/ui/user/edit_password.xml')
        return stl(handler, namespace)


    edit_password__access__ = 'is_allowed_to_edit'
    def edit_password(self, context):
        newpass = context.get_form_value('newpass')
        newpass2 = context.get_form_value('newpass2')
        password = context.get_form_value('password')
        user = context.user

        # Check input
        if self.name == user.name:
            if not self.authenticate(password):
                return context.come_back(u"You mistyped your actual password, "
                                         u"your account is not changed.")

        newpass = newpass.strip()
        if not newpass:
            return context.come_back(u'Password empty, please type one.')

        if newpass != newpass2:
            return context.come_back(u"Passwords mismatch, please try again.")

        # Clear confirmation key
        if self.has_property('ikaaro:user_must_confirm'):
            self.del_property('ikaaro:user_must_confirm')

        # Set password
        self.set_password(newpass)

        # Update the cookie if we updated our own password
        if self.name == user.name:
            self.set_auth_cookie(context, newpass)

        return context.come_back(u'Password changed.')


    #######################################################################
    # Tasks
    tasks_list__access__ = 'is_allowed_to_edit'
    tasks_list__label__ = u'Tasks'
    def tasks_list(self, context):
        root = context.root
        user = context.user

        site_root = self.get_site_root()

        namespace = {}
        documents = []

        q1 = EqQuery('workflow_state', 'pending')
        q2 = OrQuery(EqQuery('paths', site_root.get_abspath()),
                EqQuery('paths', self.get_physical_path()))
        query = AndQuery(q1, q2)

        for brain in root.search(query).get_documents():
            document = root.get_handler(brain.abspath)
            # Check security
            ac = document.get_access_control()
            if not ac.is_allowed_to_view(user, document):
                continue
            documents.append({'url': '%s/;%s' % (self.get_pathto(document),
                                                 document.get_firstview()),
                             'title': document.title_or_name})
        namespace['documents'] = documents

        handler = self.get_handler('/ui/user/tasks.xml')
        return stl(handler, namespace)


register_object_class(User)



class UserFolder(Folder):

    class_id = 'users'
    class_icon16 = 'images/UserFolder16.png'
    class_icon48 = 'images/UserFolder48.png'
    class_views = [['view'],
                   ['browse_content?mode=list'],
                   ['edit_metadata_form']]


    def get_document_types(self):
        return [get_object_class('user')]


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
            user = get_object_class('user')()
            cache[id] = user
            # Add metadata
            metadata = {'owner': id, 'ikaaro:email': email,
                        'ikaaro:password': crypt_password(password)}
            cache['%s.metadata' % id] = user.build_metadata(**metadata)


    #######################################################################
    # API
    #######################################################################

    # XXX This method should not be defined, instead we should be able to
    # label the handlers that are multilingual.
    def _get_handler_names(self):
        return BaseFolder._get_handler_names(self)


    def set_user(self, email=None, password=None):
        user = get_object_class('user')()

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

        # Add the user
        user, metadata = self.set_object(user_id, user)
        # Set the email and paswword
        if email is not None:
            user.set_property('ikaaro:email', email)
            user.set_property('dc:title', email, language='en')
        if password is not None:
            user.set_password(password)

        # Return the user
        return user


    def get_usernames(self):
        """Return all user names."""
        usernames = [ x[:-9] for x in self.get_handler_names() 
                      if x.endswith('.metadata') ]
        return frozenset(usernames)



    def del_object(self, name):
        handler = self.get_handler(name)
        if isinstance(handler, User):
            root = self.get_root()
            for group_path in handler.get_groups():
                group = root.get_handler(group_path)
                group.set_user_role(name, None)

        Folder.del_object(self, name)


    #######################################################################
    # Back-Office
    #######################################################################
    browse_content__access__ = 'is_admin'
    rename_form__access__ = False
    rename__access__ = False
    cut__access__ = False
    #remove__access__ = False
    copy__access__ = False
    paste__access__ = False

    edit_metadata_form__access__ = 'is_admin'
    edit_metadata__access__ = 'is_admin'


    #######################################################################
    # View
    view__access__ = 'is_admin'
    view__label__ = u'View'
    def view(self, context):
        message = (u'To manage the users please go '
                   u'<a href="/;permissions_form">here</a>.')
        return self.gettext(message).encode('utf-8')



register_object_class(UserFolder)
