# -*- coding: ISO-8859-1 -*-
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

# Import from itools
from itools import uri
from itools.datatypes import Email
from itools import i18n
from itools.catalog import queries
from itools.stl import stl
from itools.web import get_context
from Folder import Folder
from LocaleAware import LocaleAware
from skins import Skin
from access import RoleAware
from workflow import WorkflowAware
from users import crypt_password
from widgets import Table
from metadata import Password
from skins import ui
from registry import register_object_class



class WebSite(RoleAware, Folder):

    class_id = 'WebSite'
    class_title = u'Web Site'
    class_description = u'Create a new Web Site or Work Place.'
    class_icon16 = 'images/WebSite16.png'
    class_icon48 = 'images/WebSite48.png'
    class_views = [['browse_thumbnails', 'browse_list', 'browse_image'],
                   ['new_resource_form'],
                   ['edit_metadata_form'],
                   ['languages_form'],
                   ['permissions_form', 'anonymous_form']]

    __fixed_handlers__ = ['skin', 'index']


    __roles__ = [
        {'name': 'members', 'title': u"Members", 'unit': u"Member"},
        {'name': 'reviewers', 'title': u"Reviewers", 'unit': u"Reviewer"},
    ]


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
    # New instances
    ########################################################################
##    @classmethod
##    def new_instance_form(cls):
##        context = get_context()
##        root = context.root

##        namespace = {}
##        namespace['class_id'] = cls.class_id
##        namespace['class_title'] = cls.class_title
##        # Skins
##        skins = []
##        here = context.handler
##        templates = root.get_handler('ui/web_site_templates')
##        for name, title in [('community', cls.gettext('Community Site'))]:
##            image = templates.get_handler('%s/thumbnail.png' % name)
##            skins.append({'name': name,
##                          'title': title,
##                          'image_uri': here.get_pathto(image)})
##        namespace['skins'] = skins

##        handler = root.get_handler('ui/WebSite_new_instance.xml')
##        return stl(handler, namespace)


##    @classmethod
##    def new_instance(cls, **kw):
##        web_site = cls(**kw)

##        root = get_context().root
##        templates = root.get_handler('ui/web_site_templates')
##        template = templates.get_handler(kw['skin_name'])
##        for handler, context in template.traverse2():
##            name = handler.name
##            if name.startswith('.'):
##                context.skip = True
##            elif handler is template:
##                pass
##            elif getattr(handler, 'is_phantom', False):
##                context.skip = True
##            else:
##                path = template.get_pathto(handler)
##                properties = {}
##                if not web_site.has_handler(path):
##                    if isinstance(handler, LocaleAware):
##                        properties['dc:language'] = 'en'
##                    if isinstance(handler, WorkflowAware):
##                        properties['state'] = 'public'
##                    web_site.set_handler(path, handler, **properties)
##        return web_site


    ########################################################################
    # User interface
    ########################################################################

    permissions_form__label__ = u"Security"


    ######################################################################
    # Languages
    languages_form__access__ = 'is_allowed_to_edit'
    languages_form__label__ = u'Languages'
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

        handler = self.get_handler('/ui/Root_languages.xml')
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
    # Security / Anonymous
    anonymous_form__access__ = 'is_allowed_to_edit'
    anonymous_form__label__ = u'Security'
    anonymous_form__sublabel__ = u'Anonymous'
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


    ########################################################################
    # Register
    def is_allowed_to_register(self, user, object):
        return self.get_property('ikaaro:website_is_open')


    register_form__access__ = 'is_allowed_to_register'
    register_form__label__ = u'Register'
    def register_form(self, context):
        handler = self.get_handler('/ui/WebSite_register.xml')
        return stl(handler)


    register__access__ = 'is_allowed_to_register'
    def register(self, context):
        # Check the email
        email = context.get_form_value('ikaaro:email')
        email = email.strip()
        if not Email.is_valid(email):
            message = u'A valid email address must be provided.'
            return context.come_back(message)

        # Do we already have a user with that email?
        users = self.get_handler('users')
        if users.has_handler(email):
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
        user = users.set_user(email, password)

        # Bring the user to the login form
        message = u'Thanks for register, please log in'
        goto = ';login_form?username=%s' % email
        return context.come_back(message, goto=goto)


    ########################################################################
    # Login and logout
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
    def login(self, context):
        username = context.get_form_value('username')
        password = context.get_form_value('password')

        root = context.root
        users = root.get_handler('users')
        if username and users.has_handler(username):
            user = users.get_handler(username)
        else:
            # XXX We lost the referrer if any
            return context.come_back(
                u'The user "$username" does not exist.', username=username)

        password = crypt_password(password)
        if not user.authenticate(password):
            # XXX We lost the referrer if any
            return context.come_back(u'The password is wrong.')

        # Set cookie
        cookie = Password.encode('%s:%s' % (username, password))
        request = context.request
        expires = request.form.get('iAuthExpires', None)
        if expires is None:
            context.set_cookie('__ac', cookie, path='/')
        else:
            context.set_cookie('__ac', cookie, path='/', expires=expires)

        # Set context
        context.user = user

        referrer = request.referrer
        if referrer and referrer.path[-1].param != 'login_form':
            return referrer

        return uri.get_reference('users/%s' % user.name)


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
    # User search UI
    site_search__access__ = True
    def site_search(self, context):
        text = context.get_form_value('site_search_text').strip()
        if not text:
            return context.come_back(u"Empty search value.")

        on_title = queries.Equal('title', text)
        on_text = queries.Equal('text', text)
        query = queries.Or(on_title, on_text)
        results = self.search(query=query)

        # put the metadatas in a dictionary list to be managed with Table
        root = context.root
        fields = root.get_catalog_metadata_fields()
        table_content = []
        for result in results:
            line = {}
            for field in fields:
                # put a '' if the brain doesn't have the given field
                line[field] = getattr(result, field, '')
            table_content.append(line)

        # Build the table
        path_to_root = context.path.get_pathtoroot()
        table = Table(path_to_root, 'site_search', table_content, sortby=None,
            batchstart='0', batchsize='10')

        # get the handler for the visibles documents and extracts values
        user = context.user
        objects = []
        for object in table.objects:
            abspath = object['abspath']
            document = root.get_handler(abspath)

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

            path_to_icon = document.get_path_to_icon(16, from_handler=self)
            if path_to_icon.startswith(';'):
                path_to_icon = uri.Path('%s/' % document.name).resolve(path_to_icon)
            info['icon'] = path_to_icon

            language = object.get('language')
            if language:
                language_name = i18n.get_language_name(language)
                line['language'] = self.gettext(language_name)
            else:
                line['language'] = ''
            objects.append(info)

        table.objects = objects

        namespace = {}
        namespace['table'] = table
        namespace['batch'] = table.batch_control()

        if not objects:
            message = u'We did not find results for "%s".'
            namespace['not_found'] = self.gettext(message) % text

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


register_object_class(WebSite)
