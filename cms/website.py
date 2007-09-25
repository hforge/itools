# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from string import Template

# Import from itools
from itools.uri import Path, get_reference
from itools.datatypes import Email, Integer, Unicode
from itools.i18n import get_language_name, get_languages
from itools.catalog import EqQuery, OrQuery, AndQuery, TextField
from itools.stl import stl
from folder import Folder
from skins import Skin
from access import RoleAware
from messages import *
import widgets
from workflow import WorkflowAware
from skins import ui
from registry import (register_object_class, register_website,
    get_register_websites, get_website_class)
from utils import generate_password
from itools.rest import checkid


class WebSite(RoleAware, Folder):

    class_id = 'WebSite'
    class_title = u'Web Site'
    class_description = u'Create a new Web Site or Work Place.'
    class_icon16 = 'images/WebSite16.png'
    class_icon48 = 'images/WebSite48.png'
    class_skin = 'ui/aruni'
    class_views = [
        ['browse_content?mode=list',
         'browse_content?mode=thumbnails',
         'browse_content?mode=image'],
        ['new_resource_form'],
        ['edit_metadata_form',
         'virtual_hosts_form',
         'anonymous_form',
         'languages_form',
         'contact_options_form'],
        ['permissions_form',
         'new_user_form'],
        ['last_changes']]

    __fixed_handlers__ = ['skin', 'index']

    __roles__ = RoleAware.__roles__ + [
        # Local Administrator
        {'name': 'ikaaro:admins', 'title': u'Admin'}]


    @classmethod
    def new_instance_form(cls, context):
        namespace = {}
        namespace['websites'] = []
        namespace['class_title'] = cls.class_title
        for handler_class in get_register_websites():
            website_ns = {}
            gettext = handler_class.gettext
            title = handler_class.class_title
            website_ns['title'] = gettext(title)
            website_ns['class_id'] = handler_class.class_id
            website_ns['selected'] = False
            icon = handler_class.class_icon16
            website_ns['icon'] = context.handler.get_pathtoroot() + 'ui/' + icon
            namespace['websites'].append(website_ns)

        namespace['alone'] = False
        if len(namespace['websites']) == 1:
            namespace['alone'] = namespace['websites'][0]
        else:
            namespace['websites'][0]['selected'] = True
        handler = context.root.get_handler('ui/website/new_instance.xml')
        return stl(handler, namespace)


    @classmethod
    def new_instance(cls, container, context):
        name = context.get_form_value('name')
        title = context.get_form_value('dc:title')

        # Check the name
        name = name.strip() or title.strip()
        if not name:
            return context.come_back(MSG_NAME_MISSING)

        name = checkid(name)
        if name is None:
            return context.come_back(MSG_BAD_NAME)

        # Check the name is free
        if container.has_handler(name):
            return context.come_back(MSG_NAME_CLASH)

        class_id = context.get_form_value('class_id')
        if class_id is None:
            return context.come_back(u'Please select a website.')

        cls = get_website_class(class_id)
        # Build the object
        handler = cls()
        metadata = handler.build_metadata()
        language = container.get_site_root().get_default_language()
        metadata.set_property('dc:title', title, language=language)
        # Add the object
        handler, metadata = container.set_object(name, handler, metadata)

        goto = './%s/;%s' % (name, handler.get_firstview())
        return context.come_back(MSG_NEW_RESOURCE, goto=goto)


    def _get_virtual_handler(self, name):
        if name == 'ui':
            return ui
        elif name in ('users', 'users.metadata'):
            return self.get_handler('/%s' % name)
        return Folder._get_virtual_handler(self, name)


    ########################################################################
    # API
    ########################################################################
    def get_default_language(self):
        return self.get_property('ikaaro:website_languages')[0]


    ########################################################################
    # User interface
    ########################################################################
    edit_metadata_form__label__ = u'Edit'

    ######################################################################
    # Edit / Virtual Hosts
    virtual_hosts_form__access__ = 'is_admin'
    virtual_hosts_form__label__ = u'Edit'
    virtual_hosts_form__sublabel__ = u'Virtual Hosts'
    def virtual_hosts_form(self, context):
        namespace = {}
        vhosts = self.get_property('ikaaro:vhosts')
        namespace['vhosts'] = '\n'.join(vhosts)

        handler = self.get_handler('/ui/website/virtual_hosts.xml')
        return stl(handler, namespace)


    edit_virtual_hosts__access__ = 'is_admin'
    def edit_virtual_hosts(self, context):
        vhosts = context.get_form_value('vhosts')
        vhosts = [ x.strip() for x in vhosts.splitlines() ]
        vhosts = [ x for x in vhosts if x ]
        vhosts = tuple(vhosts)
        self.set_property('ikaaro:vhosts', vhosts)

        return context.come_back(MSG_CHANGES_SAVED)


    ######################################################################
    # Edit / Languages
    languages_form__access__ = 'is_admin'
    languages_form__label__ = u'Edit'
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

        handler = self.get_handler('/ui/website/languages.xml')
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
    # Edit / Security
    anonymous_form__access__ = 'is_allowed_to_edit'
    anonymous_form__label__ = u'Edit'
    anonymous_form__sublabel__ = u'Security Policy'
    def anonymous_form(self, context):
        # Build the namespace
        namespace = {}
        # Intranet or Extranet
        is_open = self.get_property('ikaaro:website_is_open')
        namespace['is_open'] = is_open
        namespace['is_closed'] = not is_open

        handler = self.get_handler('/ui/website/anonymous.xml')
        return stl(handler, namespace)


    edit_anonymous__access__ = 'is_allowed_to_edit'
    def edit_anonymous(self, context):
        # Boolean properties
        for name in ['ikaaro:website_is_open']:
            self.set_property(name, context.get_form_value(name, False))

        return context.come_back(MSG_CHANGES_SAVED)


    ######################################################################
    # Edit / Contact
    contact_options_form__access__ = 'is_allowed_to_edit'
    contact_options_form__label__ = u'Edit'
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
            email = user.get_property('ikaaro:email')
            if not email:
                continue
            namespace['contacts'].append(
                {'name': username,
                 'email': email,
                 'title': user.get_title(),
                 'is_selected': username in contacts})

        # Sort
        namespace['contacts'].sort(key=lambda x: x['email'])

        handler = self.get_handler('/ui/website/contact_options.xml')
        return stl(handler, namespace)


    edit_contact_options__access__ = 'is_allowed_to_edit'
    def edit_contact_options(self, context):
        contacts = context.get_form_values('contacts')
        contacts = tuple(contacts)
        self.set_property('ikaaro:contacts', contacts)

        return context.come_back(MSG_CHANGES_SAVED)


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

        handler = self.get_handler('/ui/website/register.xml')
        return stl(handler, namespace)


    register__access__ = 'is_allowed_to_register'
    def register(self, context):
        keep = ['ikaaro:firstname', 'ikaaro:lastname', 'ikaaro:email']
        # Check input data
        error = context.check_form_input(self.register_fields)
        if error is not None:
            return context.come_back(error, keep=keep)

        # Get input data
        firstname = context.get_form_value('ikaaro:firstname').strip()
        lastname = context.get_form_value('ikaaro:lastname').strip()
        email = context.get_form_value('ikaaro:email').strip()

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

        handler = self.get_handler('/ui/website/login.xml')
        return stl(handler, namespace)


    login__access__ = True
    def login(self, context, goto=None):
        email = context.get_form_value('username', type=Unicode)
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
            params = referrer.path[-1].params
            if not params:
                return referrer
            if params[0] != 'login_form':
                return referrer

        if goto is not None:
            return get_reference(goto)

        return get_reference('users/%s' % user.name)


    ########################################################################
    # Forgotten password
    forgotten_password_form__access__ = True
    def forgotten_password_form(self, context):
        handler = self.get_handler('/ui/website/forgotten_password_form.xml')
        return stl(handler)


    forgotten_password__access__ = True
    def forgotten_password(self, context):
        # TODO Don't generate the password, send instead a link to a form
        # where the user will be able to type his new password.
        root = context.root

        # Get the email address
        username = context.get_form_value('username').strip()

        # Get the user with the given login name
        results = root.search(username=username)
        if results.get_n_documents() == 0:
            message = u'There is not a user identified as "$username"'
            return context.come_back(message, username=username)

        user = results.get_documents()[0]
        user = self.get_handler('/users/%s' % user.name)

        # Send email of confirmation
        email = user.get_property('ikaaro:email')
        key = generate_password(30)
        user.set_property('ikaaro:user_must_confirm', key)
        user.send_confirmation(context, email)

        handler = self.get_handler('/ui/website/forgotten_password.xml')
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
        handler = self.get_handler('/ui/website/logout.xml')
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

        # Get and check input data
        text = context.get_form_value('site_search_text', type=Unicode)
        start = context.get_form_value('batchstart', type=Integer, default=0)

        namespace = {}
        if text.strip():
            namespace['text'] = text
            # Search
            query = [ OrQuery(EqQuery('title', word), EqQuery('text', word))
                      for word, kk in TextField.split(text) ]
            if query:
                query = AndQuery(*query)
                results = root.search(query=query)
                documents = results.get_documents()
            else:
                documents = []

            # Check access rights
            user = context.user
            handlers = []
            for object in documents:
                abspath = object.abspath
                handler = root.get_handler(abspath)
                ac = handler.get_access_control()
                if ac.is_allowed_to_view(user, handler):
                    handlers.append(handler)

            # Batch
            size = 10
            total = len(handlers)
            namespace['batch'] = widgets.batch(context.uri, start, size, total)

            # Build the namespace
            objects = []
            for handler in handlers[start:start+size]:
                abspath = handler.get_abspath()
                info = {}
                info['abspath'] = abspath
                info['title'] = handler.get_title()
                info['type'] = self.gettext(handler.class_title)
                info['size'] = handler.get_human_size()
                info['url'] = '%s/;%s' % (self.get_pathto(handler),
                                          handler.get_firstview())

                icon = handler.get_path_to_icon(16, from_handler=self)
                if icon.startswith(';'):
                    icon = Path('%s/' % handler.name).resolve(icon)
                info['icon'] = icon
                objects.append(info)
            namespace['objects'] = objects
        else:
            namespace['text'] = ''

        hander = self.get_handler('/ui/website/search.xml')
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

        handler = self.get_handler('/ui/website/search_form.xml')
        return stl(handler, namespace)


    ########################################################################
    # Contact
    contact_fields = [('to', True), ('from', True, Email), ('subject', True),
                      ('body', True)]


    contact_form__access__ = True
    def contact_form(self, context):
        # Build the namespace
        namespace = context.build_form_namespace(self.contact_fields)

        # To
        users = self.get_handler('/users')
        namespace['contacts'] = []
        for name in self.get_property('ikaaro:contacts'):
            user = users.get_handler(name)
            title = user.get_title()
            namespace['contacts'].append({'name': name, 'title': title,
                'selected': name == namespace['to']['value']})

        # From
        if namespace['from']['value'] is None:
            user = context.user
            if user is not None:
                namespace['from']['value'] = user.get_property('ikaaro:email')

        handler = self.get_handler('/ui/website/contact_form.xml')
        return stl(handler, namespace)


    contact__access__ = True
    def contact(self, context):
        # Check input data
        error = context.check_form_input(self.contact_fields)
        if error is not None:
            keep = [ x[0] for x in self.contact_fields ]
            return context.come_back(error, keep=keep)

        contact = context.get_form_value('to')
        from_addr = context.get_form_value('from').strip()
        subject = context.get_form_value('subject', type=Unicode).strip()
        body = context.get_form_value('body', type=Unicode).strip()

        # Find out the "to" address
        contact = self.get_handler('/users/%s' % contact)
        contact = contact.get_property('ikaaro:email')

        # Send the email
        root = self.get_root()
        root.send_email(from_addr, contact, subject, body)

        return context.come_back(u'Message sent.')


register_object_class(WebSite)

# Register the vanilla web site
register_website(WebSite)
