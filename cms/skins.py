# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#               2004 Jean-Philippe Robles <jpr@itaapy.com>
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
from itools import get_abspath
from itools.uri import Path, Query
from itools.datatypes import URI
from itools.handlers.File import File
from itools.xml import XML
from itools.stl import stl
from itools.xhtml import XHTML
from itools import i18n
from itools.web import get_context
from itools.web.access import AccessControl

# Import from itools.cms
from Folder import Folder
from utils import reduce_string
from widgets import tree, build_menu
from registry import register_object_class



class Skin(Folder):

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
        root = context.root
        here = context.handler or root

        menu = []
        for option in self.get_main_menu_options(context):
            path = option['path']
            method = option['method']
            title = option['title']
            src = option['icon']

            handler = root.get_handler(path)
            ac = handler.get_access_control()
            if ac.is_access_allowed(user, handler, method):
                href = '%s/;%s' % (here.get_pathto(handler), method)
                menu.append({'href': href, 'title': self.gettext(title),
                             'class': '', 'src': src, 'items': []})
    
        if not menu:
            return None

        return {'title': u'Main Menu', 'content': build_menu(menu)}


    def get_navigation_menu(self, context):
        """Build the namespace for the navigation menu."""
        menu = tree(context, depth=6, filter=Folder)
        return {'title': u'Navigation', 'content': menu}


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
        if isinstance(here, Folder):
            for handler in here.search_handlers():
                ac = handler.get_access_control()
                if not ac.is_allowed_to_view(user, handler):
                    continue
                firstview = handler.get_firstview()
                src = handler.get_path_to_icon(size=16, from_handler=here)
                options.append({'href': '%s/;%s' % (handler.name, firstview),
                                'src': src,
                                'title': handler.get_title_or_name(),
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

        #
        handlers = []
        handler = here
        while handler is not None:
            handlers.insert(0, handler)
            handler = handler.parent

        # 
        breadcrumb = []
        for handler in handlers:
            # The link
            view = handler.get_firstview()
            if view is None:
                url = None
            else:
                url = '%s/;%s' % (here.get_pathto(handler), view)
            # The title
            title = handler.get_title_or_name()
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
            return {'tabs': [], 'subtabs': []}

        # Get access control
        ac = here.get_access_control()

        # Tabs
        views = here.get_views()
        subviews = here.get_subviews(context.method)

        tabs = []
        for view in views:
            # From method?param1=value1&param2=value2&...
            # we separate method and arguments, then we get a dict with
            # the arguments and the subview active state
            if '?' in view:
                name, args = view.split('?')
                args = Query.decode(args)
                active = name == context.method or name in subviews
                for key, value in args.items():
                    request_param = request.get_parameter(key)
                    if request_param != value:
                        active = False
                        break
            else:
                name, args = view, {}
                active = name == context.method or name in subviews

            # Check security
            if not ac.is_access_allowed(user, here, name):
                continue

            # Add the menu
            label = getattr(here, '%s__label__' % name)
            if callable(label):
                label = label(**args)
            tabs.append({'id': 'tab_%s' % label.lower(),
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
                    args = Query.decode(args)
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
        return {'title': here.get_title_or_name(),
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
            root = context.root
            joinisopen = root.get_property('ikaaro:website_is_open')
            return {'info': None, 'joinisopen': joinisopen}

        home = '/users/%s/;%s' % (user.name, user.get_firstview())
        info = {'name': user.name, 'title': user.title or user.name,
                'home': home}
        return {'info': info, 'joinisopen': False}


    #######################################################################
    # Users info (context.user)
    #######################################################################
    def get_message(self, context):
        """Return a message string from de request."""
        if context.has_form_value('message'):
            message = context.get_form_value('message')
            return unicode(message, 'utf8')
        return None


    #######################################################################
    # Styles and Scripts
    #######################################################################
    def get_styles(self, context):
        styles = []
        # Epoz
        styles.append('/ui/epoz.css')
        # Calendar (http://dynarch.com/mishoo/calendar.epl)
        styles.append('/ui/calendar/calendar-aruni.css')
        # Aruni (default skin)
        styles.append('/ui/onetruelayout.css')
        styles.append('/ui/aruni/aruni.css')
        # This skin's style
        if self.has_handler('style.css'):
            styles.append('%s/style.css' % self.abspath)
        # Dynamic styles
        for style in context.styles:
            styles.append(style)

        return styles


    def get_scripts(self, context):
        scripts = []
        # Epoz
        scripts.append('/ui/epoz.js')
        # Calendar (http://dynarch.com/mishoo/calendar.epl)
        scripts.append('/ui/calendar/calendar.js')
        languages = [
            'af', 'al', 'bg', 'br', 'ca', 'da', 'de', 'du', 'el', 'en', 'es',
            'fi', 'fr', 'hr', 'hu', 'it', 'jp', 'ko', 'lt', 'lv', 'nl', 'no',
            'pl', 'pt', 'ro', 'ru', 'si', 'sk', 'sp', 'sv', 'tr', 'zh']
        accept = context.request.accept_language
        language = accept.select_language(languages)
        scripts.append('/ui/calendar/lang/calendar-%s.js' % language)
        scripts.append('/ui/calendar/calendar-setup.js')
        # Aruni (default skin)
        scripts.append('/ui/browser.js')
        scripts.append('/ui/main.js')
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
        root = context.root
        if root is here:
            return root.get_title_or_name()
        # Somewhere else
        mapping = {'root_title': root.get_title_or_name(),
                   'here_title': here.get_title_or_name()}
        return here.gettext("%(root_title)s: %(here_title)s") % mapping


    def build_namespace(self, context):
        namespace = {}

        # Resources
        namespace['styles'] = self.get_styles(context)
        namespace['scripts'] = self.get_scripts(context)

        # User menu
        namespace['user']= self.get_user_menu(context)

        # Left menus
        namespace['left_menus'] = self.get_left_menus(context)

        # Breadcrumb
        namespace['breadcrumb'] = self.get_breadcrumb(context)

        # Metadata
        namespace['metadata'] = self.get_metadata_ns(context)

        # Tabs
        namespace['tabs'] = self.get_tabs(context)

        # Message
        namespace['message'] = self.get_message(context)

        # Title
        namespace['title'] = self.get_template_title(context)

        return namespace


    def get_template(self):
        if self.has_handler('template.xhtml'):
            return self.get_handler('template.xhtml')
        # Default, aruni
        return self.get_handler('/ui/aruni/template.xhtml')


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
        s = []
        # Keep the header, but strip the XML declaration (because it makes
        # IE6 fall into quirks mode, see http://hsivonen.iki.fi/doctype/).
        # XXX There may be a better way to do this, from the API's point
        # of view.
        header = handler.header_to_str()
        header = header.split('\n', 1)[1]
        s.append(header)
        # STL
        prefix = Path(handler.get_abspath())
        data = stl(handler, namespace, prefix=prefix)
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


class UI(AccessControl, Folder):

    def is_access_allowed(self, user, object, method_name):
        return isinstance(object, File) and method_name == 'GET'


    def is_allowed_to_view(self, user, object):
        return False


    def _get_handler(self, segment, uri):
        name = segment.name
        if name in skin_registry:
            return skin_registry[name]
        return Folder._get_handler(self, segment, uri)


    def _get_virtual_handler(self, segment):
        name = segment.name
        if name in skin_registry:
            return skin_registry[name]
        return Folder._get_virtual_handler(self, segment)


path = get_abspath(globals(), 'ui')
ui = UI(path)
