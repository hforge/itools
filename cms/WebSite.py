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
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

# Import from the Standard Library
from base64 import encodestring
from urllib import quote

# Import from itools
from itools import i18n
from itools.xml.stl import stl
from itools.web import get_context

# Import from ikaaro
from exceptions import UserError
from Handler import Handler
from Folder import Folder
from LocaleAware import LocaleAware
from Metadata import Metadata
from skins import Skin
from utils import comeback
from WorkflowAware import WorkflowAware



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
    general_form__access__ = Handler.is_admin
    general_form__label__ = u'Settings'
    general_form__sublabel__ = u'General'
    def general_form(self):
        # Build the namespace
        namespace = {}
        website_is_open = self.get_property('ikaaro:website_is_open')
        namespace['website_is_open'] = website_is_open

        handler = self.get_handler('/ui/Root_general.xml')
        return stl(handler, namespace)


    change_general__access__ = Handler.is_admin
    def change_general(self, **kw):
        self.set_property('ikaaro:website_is_open',
                          kw.get('ikaaro:website_is_open', False))

        message = self.gettext(u'General settings changed')
        comeback(message)


    ######################################################################
    # Settings / Languages
    languages_form__access__ = Handler.is_admin
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


    change_default_language__access__ = Handler.is_allowed_to_edit
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


    remove_languages__access__ = Handler.is_allowed_to_edit
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


    add_language__access__ = Handler.is_allowed_to_edit
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
    def login_form(self):
        request = get_context().request
        namespace = {'referer': request.form.get('referer', ''),
                     'username': request.form.get('username', '')}

        handler = self.get_handler('/ui/WebSite_login.xml')
        return stl(handler, namespace)


    login__access__ = True
    def login(self, username, password, referer=None, **kw):
        context = get_context()
        request = context.request

        root = context.root
        users = root.get_handler('users')
        if username and users.has_handler(username):
            user = users.get_handler(username)
        else:
            # XXX We lost the referrer if any
            message = u'The user "%s" does not exist'
            raise UserError, self.gettext(message) % username

        if not user.authenticate(password):
            # XXX We lost the referrer if any
            raise UserError, self.gettext(u'The password is wrong')

        # Set cookie
        cname = '__ac'
        cookie = encodestring('%s:%s' % (username, password))
        cookie = quote(cookie)
        expires = request.form.get('iAuthExpires', None)
        if expires is None:
            context.set_cookie(cname, cookie)
        else:
            context.set_cookie(cname, cookie, expires=expires)

        # Set context
        context.user = user

        if referer:
            goto = referer
        else:
            goto = 'users/%s/;%s' % (user.name, user.get_firstview())
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
        # Redirect
        context.redirect(';' + self.get_firstview())


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


Folder.register_handler_class(WebSite)
