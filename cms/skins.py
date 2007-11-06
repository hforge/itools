# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2004 Jean-Philippe Robles <jpr@itaapy.com>
# Copyright (C) 2006-2007 Hervé Cauwelier <herve@itaapy.com>
# Copyright (C) 2006-2007 Nicolas Deram <nicolas@itaapy.com>
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from itools import get_abspath
from itools.i18n import has_language
from itools.uri import Path, decode_query
from itools.datatypes import URI
from itools.handlers import File, Folder, Database
from itools.stl import stl
from itools.web import get_context, AccessControl
from itools.xml import Parser

# Import from itools.cms
from base import Node
from folder import Folder as DBFolder
from utils import reduce_string
from widgets import tree, build_menu
from registry import register_object_class, get_object_class



class UIFolder(Node, Folder):

    def _get_object(self, name):
        if self.has_handler(name):
            handler = self.get_handler(name)
        else:
            n = len(name)
            names = [ x for x in self.get_handler_names() if x[:n] == name ]
            languages = [ x.split('.')[-1] for x in names ]
            languages = [ x for x in languages if has_language(x) ]

            if not languages:
                raise LookupError, 'XXX'

            # Get the best variant
            context = get_context()
            if context is None:
                language = None
            else:
                accept = context.get_accept_language()
                language = accept.select_language(languages)

            # By default use whatever variant
            # (XXX we need a way to define the default)
            if language is None:
                language = languages[0]
            handler = self.get_handler('%s.%s' % (name, language))

        if isinstance(handler, Folder):
            handler = UIFolder(handler.uri)
        else:
            format = handler.get_mimetype()
            handler = get_object_class(format)(handler.uri)
        handler.database = self.database
        return handler


class Skin(UIFolder):

    class_id = 'Skin'
    class_title = u'Skin'
    class_icon16 = 'images/Skin16.png'
    class_icon48 = 'images/Skin48.png'

    __fixed_handlers__ = ['template.xhtml.en']


    #######################################################################
    # Left Menu
    #######################################################################
    def get_main_menu_options(self, context):
        user = context.user

        options = []
        append = options.append
        if user is not None:
            path = '/users/%s' % user.name
            append({'path': path, 'method': 'profile', 'title': u'My Profile',
                    'icon': '/ui/aruni/images/action_home.png'})
            append({'path': path, 'method': 'browse_content',
                    'title': u'My Content',
                    'icon': '/ui/images/Folder16.png'})
        append({'path': '/', 'method': 'permissions_form',
                'title': u'Users Directory',
                'icon': '/ui/images/UserFolder16.png'})
        append({'path': '/', 'method': 'languages_form', 'title': u'Settings',
                'icon': '/ui/images/Settings16.png'})

        return options


    def get_main_menu(self, context):
        user = context.user
        root = context.site_root
        here = context.handler or root

        menu = []
        for option in self.get_main_menu_options(context):
            path = option['path']
            method = option['method']
            title = option['title']
            src = option['icon']

            handler = root.get_object(path)
            ac = handler.get_access_control()
            if ac.is_access_allowed(user, handler, method):
                href = '%s/;%s' % (here.get_pathto(handler), method)
                menu.append({'href': href, 'title': self.gettext(title),
                             'class': '', 'src': src, 'items': []})

        if not menu:
            return None

        return {'title': self.gettext(u'Main Menu'),
                'content': build_menu(menu)}


    def get_navigation_menu(self, context):
        """Build the namespace for the navigation menu."""
        from tracker import Issue

        menu = tree(context.site_root, active_node=context.handler,
                    allow=DBFolder, deny=Issue, user=context.user)
        return {'title': self.gettext(u'Navigation'), 'content': menu}


    def get_context_menu(self, context):
        # FIXME Hard-Coded
        from wiki import WikiFolder
        from tracker import Tracker

        here = context.handler
        while here is not None:
            if isinstance(here, (WikiFolder, Tracker)):
                break
            here = here.parent
        else:
            return None

        base = context.handler.get_pathto(here)

        menu = []
        for view in here.get_views():
            # Find out the title
            if '?' in view:
                name, args = view.split('?')
                args = decode_query(args)
            else:
                name, args = view, {}
            title = getattr(here, '%s__label__' % name)
            if callable(title):
                title = title(**args)
            # Append to the menu
            menu.append({'href': '%s/;%s' % (base, view),
                         'title': self.gettext(title),
                         'class': '', 'src': None, 'items': []})

        return {'title': self.gettext(here.class_title),
                'content': build_menu(menu)}


    def get_content_menu(self, context):
        here = context.handler
        user = context.user

        options = []
        # Parent
        parent = here.parent
        if parent is not None:
            firstview = parent.get_firstview()
            options.append({'href': '../;%s' % (firstview),
                            'src': None,
                            'title': '<<',
                            'class': '',
                            'items': []})

        # Content
        size = 0
        if isinstance(here, DBFolder):
            for handler in here.search_handlers():
                ac = handler.get_access_control()
                if not ac.is_allowed_to_view(user, handler):
                    continue
                firstview = handler.get_firstview()
                src = handler.get_path_to_icon(size=16, from_handler=here)
                options.append({'href': '%s/;%s' % (handler.name, firstview),
                                'src': src,
                                'title': handler.get_title(),
                                'class': '',
                                'items': []})
                size += 1

        menu = build_menu(options)
        title = Template(u'Content ($size)').substitute(size=size)

        return {'title': title, 'content': menu}


    def get_left_menus(self, context):
        menus = []
        # Main Menu
        menu = self.get_main_menu(context)
        if menu is not None:
            menus.append(menu)
        # Parent's Menu
        menu = self.get_context_menu(context)
        if menu is not None:
            menus.append(menu)
        # Navigation
        menu = self.get_navigation_menu(context)
        menus.append(menu)
        # Content
        #menu = self.get_content_menu(context)
        #menus.append(menu)

        return menus


    #######################################################################
    # Breadcrumb
    #######################################################################
    def get_breadcrumb(self, context):
        """Return a list of dicts [{name, url}...] """
        here = context.handler
        root = context.site_root

        # Build the list of handlers that make up the breadcrumb
        handlers = [root]
        for segment in context.uri.path:
            name = segment.name
            if name:
                try:
                    handler = handlers[-1].get_object(name)
                except LookupError:
                    continue
                handlers.append(handler)

        #  Build the namespace
        breadcrumb = []
        for handler in handlers:
            if not isinstance(handler, Node):
                break
            # The link
            view = handler.get_firstview()
            if view is None:
                url = None
            else:
                url = '%s/;%s' % (here.get_pathto(handler), view)
            # The title
            title = handler.get_title()
            short_title = reduce_string(title, 15, 30)
            # Name
            breadcrumb.append({'name': title, 'short_name': short_title,
                               'url': url})

        return breadcrumb


    #######################################################################
    # Tabs
    #######################################################################
    def get_tabs(self, context):
        """
        Return tabs and subtabs as a dict {tabs, subtabs} of list of dicts
        [{name, label, active, style}...].
        """
        # Get request, path, etc...
        request = context.request
        user = context.user
        here = context.handler
        if here is None:
            return []

        # Get access control
        ac = here.get_access_control()

        # Tabs
        subviews = here.get_subviews(context.method)

        tabs = []
        for view in here.get_views():
            # From method?param1=value1&param2=value2&...
            # we separate method and arguments, then we get a dict with
            # the arguments and the subview active state
            if '?' in view:
                name, args = view.split('?')
                args = decode_query(args)
                active = name == context.method or name in subviews
                for key, value in args.items():
                    request_param = request.get_parameter(key)
                    if request_param != value:
                        active = False
                        break
            else:
                name, args = view, {}
                active = name == context.method or name in subviews

            # Add the menu
            label = getattr(here, '%s__label__' % name)
            if callable(label):
                label = label(**args)
            tabs.append({'id': 'tab_%s' % label.lower().replace(' ', '_'),
                         'name': ';%s' % view,
                         'label': here.gettext(label),
                         'active': active,
                         'class': active and 'active' or None})

            # Subtabs
            subtabs = []
            for subview in here.get_subviews(view):
                # same thing, separate method and arguments
                if '?' in subview:
                    name, args = subview.split('?')
                    args = decode_query(args)
                    for key, value in args.items():
                        request_param = request.get_parameter(key)
                else:
                    name, args = subview, {}

                if ac.is_access_allowed(user, here, name):
                    label = getattr(here, '%s__sublabel__' % name)
                    if callable(label):
                        label = label(**args)
                    subtabs.append({'name': ';%s' % subview,
                                    'label': here.gettext(label)})
            tabs[-1]['options'] = subtabs

        return tabs


    #######################################################################
    # Objects metadata (context.handler)
    #######################################################################
    def get_metadata_ns(self, context):
        here = context.handler
        if here is None:
            return {'title': '',
                    'format': '',
                    'language': '',
                    'mtime': '',
                    'icon': ''}
        return {'title': here.get_title(),
                'format': here.class_title,
                'language': here.get_property('dc:language'),
                'mtime': here.get_mtime().strftime('%Y-%m-%d %H:%M'),
                'icon': here.get_path_to_icon(size=48)}


    #######################################################################
    # Users info (context.user)
    #######################################################################
    def get_user_menu(self, context):
        """Return a dict {user_icon, user, joinisopen}."""
        user = context.user

        if user is None:
            root = context.site_root
            joinisopen = root.get_property('ikaaro:website_is_open')
            return {'info': None, 'joinisopen': joinisopen}

        home = '/users/%s/;%s' % (user.name, user.get_firstview())
        info = {'name': user.name, 'title': user.get_title(),
                'home': home}
        return {'info': info, 'joinisopen': False}


    #######################################################################
    # Users info (context.user)
    #######################################################################
    def get_message(self, context):
        """Return a message string from de request."""
        if context.has_form_value('message'):
            message = context.get_form_value('message')
            return Parser(message)
        return None


    #######################################################################
    # Styles and Scripts
    #######################################################################
    def get_styles(self, context):
        styles = []
        # Epoz
        styles.append('/ui/epoz/style.css')
        # Calendar JavaScript Widget (http://dynarch.com/mishoo/calendar.epl)
        styles.append('/ui/calendar/calendar-aruni.css')
        # Aruni (default skin)
        styles.append('/ui/aruni/aruni.css')
        # Calendar
        styles.append('/ui/ical/calendar.css')
        # Table
        styles.append('/ui/table/style.css')
        # This skin's style
        if self.has_handler('style.css'):
            styles.append('%s/style.css' % self.abspath)
        # Dynamic styles
        for style in context.styles:
            styles.append(style)

        return styles


    def get_scripts(self, context):
        scripts = []
        # Aruni (default skin)
        scripts.append('/ui/browser.js')
        scripts.append('/ui/main.js')
        # Epoz
        scripts.append('/ui/epoz/javascript.js')
        # Calendar (http://dynarch.com/mishoo/calendar.epl)
        scripts.append('/ui/calendar/calendar.js')
        languages = [
            'af', 'al', 'bg', 'br', 'ca', 'da', 'de', 'du', 'el', 'en', 'es',
            'fi', 'fr', 'hr', 'hu', 'it', 'jp', 'ko', 'lt', 'lv', 'nl', 'no',
            'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sp', 'sv', 'tr', 'zh']
        accept = context.get_accept_language()
        language = accept.select_language(languages)
        scripts.append('/ui/calendar/lang/calendar-%s.js' % language)
        scripts.append('/ui/calendar/calendar-setup.js')
        # Table
        scripts.append('/ui/table/javascript.js')
        # This skin's JavaScript
        if self.has_handler('javascript.js'):
            scripts.append('%s/javascript.js' % self.abspath)
        # Dynamic scripts
        for script in context.scripts:
            scripts.append(script)

        return scripts


    #######################################################################
    #
    #######################################################################
    def get_template_title(self, context):
        """Return the title to give to the template document."""
        here = context.handler
        # Not Found
        if here is None:
            return u'404 Not Found'
        # In the Root
        root = here.get_site_root()
        if root is here:
            return root.get_title()
        # Somewhere else
        mapping = {'root_title': root.get_title(),
                   'here_title': here.get_title()}
        return here.gettext("%(root_title)s: %(here_title)s") % mapping


    def get_meta_tags(self, context):
        """Return a list of dict with meta tags to give to the template
        document.
        """
        here = context.handler
        root = here.get_site_root()

        meta = []
        # Set description
        value, language = here.get_property_and_language('dc:description')
        if value:
            meta.append({'name': 'description', 'lang': language,
                         'content': value})
        # Set keywords for all languages
        for language in root.get_property('ikaaro:website_languages'):
            value = here.get_property('dc:subject', language).strip()
            if value:
                meta.append({'name': 'keywords', 'lang': language,
                             'content': value})
        return meta


    def build_namespace(self, context):
        namespace = {}
        # CSS & JavaScript
        namespace['styles'] = self.get_styles(context)
        namespace['scripts'] = self.get_scripts(context)
        # Title & Meta
        namespace['title'] = self.get_template_title(context)
        namespace['meta_tags']= self.get_meta_tags(context)
        # User menu
        namespace['user']= self.get_user_menu(context)
        # Left menus
        namespace['left_menus'] = self.get_left_menus(context)
        # Object's metadata & Breadcrumb
        namespace['metadata'] = self.get_metadata_ns(context)
        namespace['breadcrumb'] = self.get_breadcrumb(context)
        # Tabs & Message
        namespace['tabs'] = self.get_tabs(context)
        namespace['message'] = self.get_message(context)
        # View's title
        here = context.handler
        title = getattr(here, '%s__title__' % context.method, None)
        if title is None:
            namespace['view_title'] = None
        else:
            namespace['view_title'] = here.gettext(title)

        return namespace


    def get_template(self):
        try:
            return self.get_object('template.xhtml')
        except LookupError:
            # Default, aruni
            return self.get_object('/ui/aruni/template.xhtml')


    def template(self, content):
        context = get_context()
        # Build the namespace
        namespace = self.build_namespace(context)
        namespace['body'] = content

        # Set the encoding to UTF-8
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        # Load the template
        handler = self.get_template()

        # Build the output
        s = ['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"\n'
             '  "http://www.w3.org/TR/html4/strict.dtd">']
        # STL
        prefix = Path(handler.get_abspath())
        data = stl(handler, namespace, prefix=prefix, mode='html')
        s.append(data)

        return ''.join(s)


register_object_class(Skin)


#############################################################################
# The folder "/ui"
#############################################################################

skin_registry = {}
def register_skin(name, skin):
    if isinstance(skin, str):
        skin = Skin(skin)
    skin_registry[name] = skin


# Register the built-in skins
path = get_abspath(globals(), 'ui')
register_skin('aruni', '%s/aruni' % path)


class UI(AccessControl, UIFolder):

    def is_access_allowed(self, user, object, method_name):
        return isinstance(object, File) and method_name == 'GET'


    def is_allowed_to_view(self, user, object):
        return False


    def _get_object(self, name):
        if name in skin_registry:
            skin = skin_registry[name]
            skin.database = self.database
            return skin
        return UIFolder._get_object(self, name)


path = get_abspath(globals(), 'ui')
ui = UI(path)
ui.database = Database()
