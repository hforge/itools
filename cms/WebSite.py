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
from base64 import encodestring
from urllib import quote

# Import from itools
from itools import uri
from itools import i18n
from itools.xml.stl import stl
from itools.web import get_context
from itools.web.exceptions import UserError

# Import from ikaaro
from Handler import Handler
from Folder import Folder
from LocaleAware import LocaleAware
from Metadata import Metadata
from skins import Skin
from utils import comeback
from workflow import WorkflowAware
from widgets import Table



class WebSite(Folder):

    class_id = 'WebSite'
    class_title = u'Web Site'
    class_description = u'...'
    class_icon16 = 'images/WebSite16.png'
    class_icon48 = 'images/WebSite48.png'

    __fixed_handlers__ = ['skin', 'index']


    def get_skeleton(self, skin_name=None, **kw):
        skeleton = {}
        # The Skin
        skin = Skin()
        skeleton['skin'] = skin
        skeleton['.skin.metadata'] = self.build_metadata(skin, **kw)

        return skeleton


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
##            elif name.endswith('~'):
##                pass
##            elif handler.real_handler is not None:
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
    def get_views(self):
        return ['browse_thumbnails', 'new_resource_form', 'edit_metadata_form',
                'general_form']


    def get_subviews(self, name):
        if name in ['general_form', 'languages_form']:
            return ['general_form', 'languages_form']
        return Folder.get_subviews(self, name)


    ######################################################################
    # Settings / General
    general_form__access__ = 'is_admin'
    general_form__label__ = u'Settings'
    general_form__sublabel__ = u'General'
    def general_form(self):
        # Build the namespace
        namespace = {}
        website_is_open = self.get_property('ikaaro:website_is_open')
        namespace['website_is_open'] = website_is_open

        handler = self.get_handler('/ui/Root_general.xml')
        return stl(handler, namespace)


    change_general__access__ = 'is_admin'
    def change_general(self, **kw):
        self.set_property('ikaaro:website_is_open',
                          kw.get('ikaaro:website_is_open', False))

        message = self.gettext(u'General settings changed.')
        comeback(message)


    ######################################################################
    # Settings / Languages
    languages_form__access__ = 'is_admin'
    languages_form__label__ = u'Languages'
    languages_form__sublabel__ = u'Languages'
    def languages_form(self):
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
    def change_default_language(self, codes=[], **kw):
        if len(codes) != 1:
            message = u'You must select one and only one language.'
            raise UserError, self.gettext(message)

        website_languages = self.get_property('ikaaro:website_languages')
        website_languages = [codes[0]] + [ x for x in website_languages
                                           if x != codes[0] ]
        self.set_property('ikaaro:website_languages',
                          tuple(website_languages))

        message = self.gettext(u'The default language has been changed.')
        comeback(message)


    remove_languages__access__ = 'is_allowed_to_edit'
    def remove_languages(self, codes=[], **kw):
        website_languages = self.get_property('ikaaro:website_languages')
        default_language = website_languages[0]

        if default_language in codes:
            message = u'You can not remove the default language.'
            raise UserError, self.gettext(message)

        website_languages = [ x for x in website_languages if x not in codes ]
        self.set_property('ikaaro:website_languages',
                          tuple(website_languages))

        message = self.gettext(u'Languages removed.')
        comeback(message)


    add_language__access__ = 'is_allowed_to_edit'
    def add_language(self, code=None, **kw):
        if not code:
            raise UserError, self.gettext(u'You must choose a language')

        website_languages = self.get_property('ikaaro:website_languages')
        self.set_property('ikaaro:website_languages',
                          website_languages + (code,))

        message = self.gettext(u'Language added.')
        comeback(message)


    ########################################################################
    # Login and logout
    # XXX Fix the spelling: "referer" -> "referrer"
    login_form__access__ = True
    login_form__label__ = u'Login'
    def login_form(self, **kw):
        context = get_context()

        namespace = {}
        here = context.handler
        site_root = here.get_site_root()
        namespace['action'] = '%s/;login' % here.get_pathto(site_root)
        namespace['username'] = kw.get('username', '')

        handler = self.get_handler('/ui/WebSite_login.xml')
        return stl(handler, namespace)


    login__access__ = True
    def login(self, username, password, **kw):
        context = get_context()
        request = context.request

        root = context.root
        users = root.get_handler('users')
        if username and users.has_handler(username):
            user = users.get_handler(username)
        else:
            # XXX We lost the referrer if any
            message = u'The user "%s" does not exist.'
            raise UserError, self.gettext(message) % username

        if not user.authenticate(password):
            # XXX We lost the referrer if any
            raise UserError, self.gettext(u'The password is wrong.')

        # Set cookie
        cname = '__ac'
        cookie = encodestring('%s:%s' % (username, password))
        cookie = quote(cookie)
        path = '/'
        expires = request.form.get('iAuthExpires', None)
        if expires is None:
            context.set_cookie(cname, cookie, path=path)
        else:
            context.set_cookie(cname, cookie, path=path, expires=expires)

        # Set context
        context.user = user

        referrer = request.referrer
        if referrer and referrer.path[-1].param != 'login_form':
            goto = referrer
        else:
            goto = 'users/' + user.name
        context.redirect(goto)


    logout__access__ = True
    def logout(self):
        """
        Logs out of the application.
        """
        context = get_context()

        # Remove the cookie
        context.del_cookie('__ac')
        # Remove the user from the context
        context.user = None
        # Say goodbye
        handler = self.get_handler('/ui/WebSite_logout.xml')
        return stl(handler)


    ########################################################################
    # Error page
    error_page__access__ = True
    def error_page(self):
        context = get_context()
        form = context.request.form
        handler = self.get_handler('/ui/WebSite_error_page.xml')
        namespace = {}
        namespace['error_log'] = form.get('error_log')
        return stl(handler, namespace)


    ########################################################################
    # Languages
    change_language__access__ = True
    def change_language(self, lang, goto=None, **kw):
        context = get_context()
        context.set_cookie('language', lang)

        # Comes back
        if goto is None:
            goto = context.request.referrer

        context.redirect(goto)

    
    ########################################################################
    # User search UI
    site_search__access__ = True
    def site_search(self, **kw):
        from itools.catalog import Query

        context = get_context()
        root = context.root

        text = kw.get('site_search_text', '').strip()
        if not text:
            raise UserError, "Empty search value."

        on_title = Query.Equal('title', text)
        on_text = Query.Equal('text', text)
        query = Query.Or(on_title, on_text)
        results = self.search(query=query)

        # put the metadatas in a dictionary list to be managed with Table
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
        objects = []
        for object in table.objects:
            abspath = object['abspath']
            document = root.get_handler(abspath)
            
            if not document.is_allowed_to_view():
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
    def site_search_form(self, **kw):
        context = get_context()

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
      

Folder.register_handler_class(WebSite)
