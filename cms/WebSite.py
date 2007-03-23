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
from string import Template

# Import from itools
from itools.uri import Path, get_reference
from itools.datatypes import Email, Integer, Unicode
from itools.i18n import get_language_name, get_languages
from itools.catalog import Equal, Or
from itools.stl import stl
from Folder import Folder
from skins import Skin
from access import RoleAware
from workflow import WorkflowAware
from skins import ui
from registry import register_object_class
from utils import generate_password



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
        ['permissions_form', 'new_user_form'],
        ['last_changes']]

    __fixed_handlers__ = ['skin', 'index']

    __roles__ = RoleAware.__roles__ + [
        # Local Administrator
        {'name': 'ikaaro:admins', 'title': u'Admins', 'unit': u'Admin'}]


    def _get_virtual_handler(self, name):
        if name == 'ui':
            return ui
        elif name in ('users', 'users.metadata'):
            return self.get_handler('/%s' % name)
        return Folder._get_virtual_handler(self, name)


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
            language_name = get_language_name(code)
            languages.append({'code': code,
                              'name': self.gettext(language_name),
                              'isdefault': code == default_language})
        namespace['active_languages'] = languages

        # List of non active languages
        languages = []
        for language in get_languages():
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
        # Intranet or Extranet
        is_open = self.get_property('ikaaro:website_is_open')
        namespace['is_open'] = is_open
        namespace['is_closed'] = not is_open

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
        for username in users.get_usernames():
            user = users.get_handler(username)
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
                       ('ikaaro:email', True)]


    register_form__access__ = 'is_allowed_to_register'
    register_form__label__ = u'Register'
    def register_form(self, context):
        namespace = context.build_form_namespace(self.register_fields)

        handler = self.get_handler('/ui/WebSite_register.xml')
        return stl(handler, namespace)


    register__access__ = 'is_allowed_to_register'
    def register(self, context):
        keep = ['ikaaro:firstname', 'ikaaro:lastname', 'ikaaro:email']
        # Check input data
        error = context.check_form_input(self.register_fields)
        if error is not None:
            return context.come_back(error, keep=keep)

        # Check the real name
        firstname = context.get_form_value('ikaaro:firstname').strip()
        lastname = context.get_form_value('ikaaro:lastname').strip()

        # Check the email
        email = context.get_form_value('ikaaro:email')
        email = email.strip()
        if not Email.is_valid(email):
            message = u'A valid email address must be provided.'
            return context.come_back(message, keep=keep)

        # Do we already have a user with that email?
        root = context.root
        results = root.search(email=email)
        users = self.get_handler('users')
        if results.get_n_documents():
            user = results.get_documents()[0]
            user = users.get_handler(user.name)
            if not user.has_property('ikaaro:user_must_confirm'):
                message = u'There is already an active user with that email.'
                return context.come_back(message, keep=keep)
        else:
            # Add the user
            user = users.set_user(email, None)
            user.set_property('ikaaro:firstname', firstname, language='en')
            user.set_property('ikaaro:lastname', lastname, language='en')
            # Set the role
            default_role = self.__roles__[0]['name']
            self.set_user_role(user.name, default_role)
            # Reindex
            root.reindex_handler(user)

        # Send confirmation email
        key = generate_password(30)
        user.set_property('ikaaro:user_must_confirm', key)
        user.send_confirmation(context, email)

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
        keep = ['username']

        # Check the email field has been filed
        email = email.strip()
        if not email:
            message = u'Type your email please.'
            return context.come_back(message, keep=keep)

        # Check the user exists
        root = context.root

        # Search the user by username (login name)
        results = root.search(username=email)
        if results.get_n_documents() == 0:
            message = u'The user "$username" does not exist.'
            return context.come_back(message, username=email, keep=keep)

        # Get the user
        brain = results.get_documents()[0]
        user = root.get_handler('users/%s' % brain.name)

        # Check the user is active
        if user.get_property('ikaaro:user_must_confirm'):
            message = u'The user "$username" is not active.'
            return context.come_back(message, username=email, keep=keep)

        # Check the password is right
        if not user.authenticate(password):
            return context.come_back(u'The password is wrong.', keep=keep)

        # Set cookie
        user.set_auth_cookie(context, password)

        # Set context
        context.user = user

        # Come back
        referrer = context.request.referrer
        if referrer:
            if not referrer.path:
                return referrer
            elif referrer.path[-1].params[0] != 'login_form':
                return referrer

        if goto is not None:
            return get_reference(goto)

        return get_reference('users/%s' % user.name)


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
        results = root.search(email=email)
        if results.get_n_documents() == 0:
            message = u'There is not a user with the email address "$email"'
            return context.come_back(message, email=email)

        user = results.get_documents()[0]
        user = self.get_handler('/users/%s' % user.name)

        # Generate the password
        password = generate_password()

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
        root = context.root

        namespace = {}
        # Get and check input data
        text = context.get_form_value('site_search_text', default='').strip()
        text = Unicode.decode(text)
        namespace['site_search_text'] = text
        # Batch
        start = context.get_form_value('start', type=Integer, default=0)
        size = 10

        # Search
        on_title = Equal('title', text)
        on_text = Equal('text', text)
        query = Or(on_title, on_text)
        results = root.search(query=query)
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
        subject = context.get_form_value('subject', type=Unicode).strip()
        body = context.get_form_value('body', type=Unicode).strip()

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
