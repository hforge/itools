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
from copy import deepcopy
import random
from string import ascii_letters, Template

# Import from itools
from itools import uri
from itools.uri import Path
from itools.datatypes import Email, Integer, Unicode
from itools import i18n
from itools.catalog import queries
from itools.stl import stl
from itools.web import get_context
from Folder import Folder
from skins import Skin
from access import RoleAware
from workflow import WorkflowAware
from users import crypt_password
from metadata import Password
from skins import ui
from registry import register_object_class



class WebSite(RoleAware, Folder):

    class_id = 'WebSite'
    class_title = u'Web Site'
    class_description = u'Create a new Web Site or Work Place.'
    class_icon16 = 'images/WebSite16.png'
    class_icon48 = 'images/WebSite48.png'
    class_views = [
        ['browse_content?mode=thumbnails',
         'browse_content?mode=list',
         'browse_content?mode=image'],
        ['new_resource_form'],
        ['edit_metadata_form'],
        ['languages_form', 'anonymous_form', 'contact_options_form'],
        ['permissions_form', 'new_user_form']]

    __fixed_handlers__ = ['skin', 'index']


##    def get_skeleton(self, skin_name=None, **kw):
##        skeleton = {}
##        # The Skin
##        skin = Skin()
##        skeleton['skin'] = skin
##        skeleton['skin.metadata'] = self.build_metadata(skin, **kw)

##        return skeleton


    def _get_virtual_handler(self, segment):
        name = segment.name
        if name == 'ui':
            return ui
        elif name in ('users', 'users.metadata'):
            return self.get_handler('/%s' % name)
        return Folder._get_virtual_handler(self, segment)


    ########################################################################
    # User interface
    ########################################################################

    ######################################################################
    # Settings / Languages
    languages_form__access__ = 'is_admin'
    languages_form__label__ = u'Settings'
    languages_form__sublabel__ = u'Languages'
    def languages_form(self, context):
        namespace = {}

        # List of active languages
        languages = []
        website_languages = self.get_property('ikaaro:website_languages')
        default_language = website_languages[0]
        for code in website_languages:
            language_name = i18n.get_language_name(code)
            languages.append({'code': code,
                              'name': self.gettext(language_name),
                              'isdefault': code == default_language})
        namespace['active_languages'] = languages

        # List of non active languages
        languages = []
        for language in i18n.get_languages():
            code = language['code']
            if code not in website_languages:
                languages.append({'code': code,
                                  'name': self.gettext(language['name'])})
        languages.sort(lambda x, y: cmp(x['name'], y['name']))
        namespace['non_active_languages'] = languages

        handler = self.get_handler('/ui/WebSite_languages.xml')
        return stl(handler, namespace)


    change_default_language__access__ = 'is_allowed_to_edit'
    def change_default_language(self, context):
        codes = context.get_form_values('codes')
        if len(codes) != 1:
            return context.come_back(
                u'You must select one and only one language.')

        website_languages = self.get_property('ikaaro:website_languages')
        website_languages = [codes[0]] + [ x for x in website_languages
                                           if x != codes[0] ]
        self.set_property('ikaaro:website_languages',
                          tuple(website_languages))

        return context.come_back(u'The default language has been changed.')


    remove_languages__access__ = 'is_allowed_to_edit'
    def remove_languages(self, context):
        codes = context.get_form_values('codes')
        website_languages = self.get_property('ikaaro:website_languages')
        default_language = website_languages[0]

        if default_language in codes:
            return context.come_back(
                u'You can not remove the default language.')

        website_languages = [ x for x in website_languages if x not in codes ]
        self.set_property('ikaaro:website_languages',
                          tuple(website_languages))

        return context.come_back(u'Languages removed.')


    add_language__access__ = 'is_allowed_to_edit'
    def add_language(self, context):
        code = context.get_form_value('code')
        if not code:
            return context.come_back(u'You must choose a language')

        website_languages = self.get_property('ikaaro:website_languages')
        self.set_property('ikaaro:website_languages',
                          website_languages + (code,))

        return context.come_back(u'Language added.')


    ######################################################################
    # Settings / Registration
    anonymous_form__access__ = 'is_allowed_to_edit'
    anonymous_form__label__ = u'Settings'
    anonymous_form__sublabel__ = u'Registration'
    def anonymous_form(self, context):
        # Build the namespace
        namespace = {}
        # Monolingual properties
        for name in ['ikaaro:website_is_open']:
            namespace[name] = self.get_property(name)

        handler = self.get_handler('/ui/WebSite_anonymous.xml')
        return stl(handler, namespace)


    edit_anonymous__access__ = 'is_allowed_to_edit'
    def edit_anonymous(self, context):
        # Boolean properties
        for name in ['ikaaro:website_is_open']:
            self.set_property(name, context.get_form_value(name, False))

        return context.come_back(u'Changes saved.')


    ######################################################################
    # Settings / Contact
    contact_options_form__access__ = 'is_allowed_to_edit'
    contact_options_form__label__ = u'Settings'
    contact_options_form__sublabel__ = u'Contact'
    def contact_options_form(self, context):
        # Find out the contacts
        contacts = self.get_property('ikaaro:contacts')

        # Build the namespace
        users = self.get_handler('/users')

        namespace = {}
        namespace['contacts'] = []
        for user in users.search_handlers():
            username = user.name
            title = user.get_title_or_name()
            email = user.get_property('ikaaro:email')
            if not email:
                continue
            namespace['contacts'].append(
                {'name': username, 'email': email,
                 'title': title, 'is_selected': username in contacts})

        # Sort
        namespace['contacts'].sort(key=lambda x: x['email'])

        handler = self.get_handler('/ui/WebSite_contact_options.xml')
        return stl(handler, namespace)


    edit_contact_options__access__ = 'is_allowed_to_edit'
    def edit_contact_options(self, context):
        contacts = context.get_form_values('contacts')
        contacts = tuple(contacts)
        self.set_property('ikaaro:contacts', contacts)

        return context.come_back(u'Changes saved.')


    ########################################################################
    # Register
    def is_allowed_to_register(self, user, object):
        return self.get_property('ikaaro:website_is_open')


    register_fields = [('ikaaro:firstname', True),
                       ('ikaaro:lastname', True),
                       ('ikaaro:email', True),
                       ('password', True),
                       ('password2', True)]


    register_form__access__ = 'is_allowed_to_register'
    register_form__label__ = u'Register'
    def register_form(self, context):
        namespace = context.build_form_namespace(self.register_fields)

        handler = self.get_handler('/ui/WebSite_register.xml')
        return stl(handler, namespace)


    register__access__ = 'is_allowed_to_register'
    def register(self, context):
        # Check input data
        error = context.check_form_input(self.register_fields)
        if error is not None:
            return context.come_back(error)

        # Check the real name
        firstname = context.get_form_value('ikaaro:firstname').strip()
        lastname = context.get_form_value('ikaaro:lastname').strip()

        # Check the email
        email = context.get_form_value('ikaaro:email')
        email = email.strip()
        if not Email.is_valid(email):
            message = u'A valid email address must be provided.'
            return context.come_back(message)

        # Do we already have a user with that email?
        root = context.root
        catalog = root.get_handler('.catalog')
        results = catalog.search(email=email)
        if results.get_n_documents():
            message = u'There is already a user with that email.'
            return context.come_back(message)

        # Check the password
        password = context.get_form_value('password')
        if not password:
            message = u'The password is mandatory.'
            return context.come_back(message)

        # Check the password
        password2 = context.get_form_value('password2')
        if password != password2:
            message = u'The passwords do not match.'
            return context.come_back(message)

        # Add the user
        users = self.get_handler('users')
        user = users.set_user(email, password)
        key = ''.join([ random.choice(ascii_letters) for x in range(30) ])
        user.set_property('ikaaro:user_must_confirm', key)
        user.set_property('ikaaro:firstname', firstname, language='en')
        user.set_property('ikaaro:lastname', lastname, language='en')

        # Send confirmation email
        subject = self.gettext("Register confirmation required.")
        body = self.gettext(
            "To confirm your registration click the link:\n"
            "\n"
            "  $confirm_url")
        confirm_url = deepcopy(context.uri)
        confirm_url.path = Path('/users/%s/;confirm_registration' % user.name)
        confirm_url.query = {
            'key': user.get_property('ikaaro:user_must_confirm')}
        body = Template(body).substitute({'confirm_url': str(confirm_url)})
        root.send_email(None, email, subject, body)

        # Reindex
        root.reindex_handler(user)

        # Bring the user to the login form
        message = self.gettext(
            u"An email has been sent to you, to finish the registration "
            u"process follow the instructions detailed in it.")
        return message.encode('utf-8')


    ########################################################################
    # Login
    login_form__access__ = True
    login_form__label__ = u'Login'
    def login_form(self, context):
        namespace = {}
        here = context.handler
        site_root = here.get_site_root()
        namespace['action'] = '%s/;login' % here.get_pathto(site_root)
        namespace['username'] = context.get_form_value('username')

        handler = self.get_handler('/ui/WebSite_login.xml')
        return stl(handler, namespace)


    login__access__ = True
    def login(self, context, goto=None):
        email = context.get_form_value('username')
        password = context.get_form_value('password')

        # Don't send back the password
        keys = ['password']

        # Check the email field has been filed
        email = email.strip()
        if not email:
            message = u'Type your email please.'
            return context.come_back(message, exclude=keys)

        # Check the user exists
        root = context.root
        catalog = root.get_handler('.catalog')

        # Search first by the username, then by the email (for backwards
        # compatibility with 0.14)
        results = catalog.search(username=email)
        if results.get_n_documents() == 0:
            results = catalog.search(email=email)
            # No user found
            if results.get_n_documents() == 0:
                message = u'The user "$username" does not exist.'
                return context.come_back(message, username=email, exclude=keys)

        # Get the user
        brain = results.get_documents()[0]
        user = root.get_handler('users/%s' % brain.name)

        # Check the user is active
        if user.get_property('ikaaro:user_must_confirm'):
            message = u'The user "$username" is not active.'
            return context.come_back(message, username=email, exclude=keys)

        # Check the password is right
        password = crypt_password(password)
        if not user.authenticate(password):
            return context.come_back(u'The password is wrong.', exclude=keys)

        # Set cookie
        username = str(user.name)
        cookie = Password.encode('%s:%s' % (username, password))
        request = context.request
        expires = request.form.get('iAuthExpires', None)
        if expires is None:
            context.set_cookie('__ac', cookie, path='/')
        else:
            context.set_cookie('__ac', cookie, path='/', expires=expires)

        # Set context
        context.user = user

        # Come back
        referrer = request.referrer
        if referrer:
            if not referrer.path:
                return referrer
            elif referrer.path[-1].param != 'login_form':
                return referrer

        if goto is not None:
            return uri.get_reference(goto)

        return uri.get_reference('users/%s' % user.name)


    ########################################################################
    # Forgotten password
    forgotten_password_form__access__ = True
    def forgotten_password_form(self, context):
        handler = self.get_handler('/ui/WebSite_forgotten_password_form.xml')
        return stl(handler)


    forgotten_password__access__ = True
    def forgotten_password(self, context):
        # TODO Don't generate the password, send instead a link to a form
        # where the user will be able to type his new password.
        root = context.root

        # Get the email address
        email = context.get_form_value('ikaaro:email')

        # Get the user with the given email address
        catalog = root.get_handler('.catalog')
        results = catalog.search(email=email)
        if results.get_n_documents() == 0:
            message = u'There is not a user with the email address "$email"'
            return context.come_back(message, email=email)

        user = results.get_documents()[0]
        user = self.get_handler('/users/%s' % user.name)

        # Generate the password
        password = ''.join([ random.choice(ascii_letters) for x in range(6) ])

        # Send the email
        subject = u"Forgotten password"
        body = self.gettext(
            u"Your new password:\n"
            u"\n"
            u"  $password")
        body = Template(body).substitute({'password': password})
        root.send_email(None, email, subject, body)

        # Change the password
        user.set_password(password)

        handler = self.get_handler('/ui/WebSite_forgotten_password.xml')
        return stl(handler)


    ########################################################################
    # Logout
    logout__access__ = True
    def logout(self, context):
        """Logs out of the application."""
        # Remove the cookie
        context.del_cookie('__ac')
        # Remove the user from the context
        context.user = None
        # Say goodbye
        handler = self.get_handler('/ui/WebSite_logout.xml')
        return stl(handler)


    ########################################################################
    # Languages
    change_language__access__ = True
    def change_language(self, context):
        lang = context.get_form_value('lang')
        goto = context.get_form_value('goto', context.request.referrer)

        context.set_cookie('language', lang)
        return goto

    
    ########################################################################
    # Search
    site_search__access__ = True
    def site_search(self, context):
        namespace = {}
        # Get and check input data
        text = context.get_form_value('site_search_text', default='').strip()
        text = Unicode.decode(text)
        namespace['site_search_text'] = text
        # Batch
        start = context.get_form_value('start', type=Integer, default=0)
        size = 10

        # Search
        on_title = queries.Equal('title', text)
        on_text = queries.Equal('text', text)
        query = queries.Or(on_title, on_text)
        results = self.search(query=query)
        documents = results.get_documents(start=start, size=size)

        # put the metadatas in a dictionary list to be managed with Table
        root = context.root

        # Get the handler for the visibles documents and extracts values
        user = context.user
        objects = []
        for object in documents:
            abspath = object.abspath
            document = root.get_handler(abspath)

            # XXX The access control check should be done for the entire
            # set, but it would be too slow.
            ac = document.get_access_control()
            if not ac.is_allowed_to_view(user, document):
                continue

            info = {}
            info['abspath'] = abspath
            info['title'] = document.title_or_name
            info['type'] = self.gettext(document.class_title)
            info['size'] = document.get_human_size()
            info['url'] = '%s/;%s' % (self.get_pathto(document),
                    document.get_firstview())

            icon = document.get_path_to_icon(16, from_handler=self)
            if icon.startswith(';'):
                icon = Path('%s/' % document.name).resolve(icon)
            info['icon'] = icon
            objects.append(info)

        total = results.get_n_documents()
        end = start + len(documents)

        namespace['total'] = total
        namespace['objects'] = objects
        namespace['batchstart'] = start + 1
        namespace['batchend'] = end
        namespace['batch_previous'] = None
        if start > 0:
            prev = max(start - size, 0)
            prev = str(prev)
            namespace['batch_previous'] = context.uri.replace(start=prev)
        namespace['batch_next'] = None
        if end < total:
            next = str(end)
            namespace['batch_next'] = context.uri.replace(start=next)
        namespace['text'] = text

        hander = self.get_handler('/ui/WebSite_search.xml')
        return stl(hander, namespace)


    site_search_form__access__ = True
    def site_search_form(self, context):
        namespace = {}

        states = []
        if context.user is not None:
            workflow = WorkflowAware.workflow
            for name, state in workflow.states.items():
                title = state['title'] or name
                states.append({'key': name, 'value': title})
        namespace['states'] = states

        icon = self.get_handler('/ui/images/button_calendar.png')
        namespace['button_calendar'] = self.get_pathto(icon)

        handler = self.get_handler('/ui/WebSite_search_form.xml')
        return stl(handler, namespace)


    ########################################################################
    # Contact
    contact_form__access__ = True
    def contact_form(self, context):
        # Build the namespace
        namespace = {}

        # To
        users = self.get_handler('/users')
        namespace['contacts'] = []
        for name in self.get_property('ikaaro:contacts'):
            user = users.get_handler(name)
            email = user.get_property('ikaaro:email').replace('@', '&nbsp;@ ')
            title = user.get_title() or email
            namespace['contacts'].append({'name': name, 'title': title})

        # From
        user = context.user
        if user is None:
            namespace['from'] = None
        else:
            namespace['from'] = user.get_property('ikaaro:email')

        handler = self.get_handler('/ui/WebSite_contact_form.xml')
        return stl(handler, namespace)


    contact__access__ = True
    def contact(self, context):
        contact = context.get_form_value('to')
        from_addr = context.get_form_value('from').strip()
        subject = context.get_form_value('subject').strip()
        body = context.get_form_value('body').strip()

        # Check the input data
        if not contact or not from_addr or not subject or not body:
            return context.come_back(u'Please fill the missing fields.')

        # Check the from address
        if not Email.is_valid(from_addr):
            return context.come_back(u'A valid email address must be provided.')

        # Find out the "to" address
        contact = self.get_handler('/users/%s' % contact)
        contact = contact.get_property('ikaaro:email')

        # Send the email
        root = self.get_root()
        root.send_email(from_addr, contact, subject, body)

        return context.come_back(u'Message sent.')


register_object_class(WebSite)
