# -*- coding: ISO-8859-1 -*-
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
from time import time
from operator import itemgetter

# Import from itools
from itools import uri
from itools import get_abspath
from itools.datatypes import URI
from itools.resources import get_resource, memory
from itools.xml import XML
from itools.xml.stl import stl
from itools.xhtml import XHTML
from itools import i18n
from itools.web import get_context

# Import from itools.cms
from Folder import Folder
from utils import reduce_string



class Skin(Folder):

    class_id = 'Skin'
    class_title = u'Skin'
    class_icon16 = 'images/Skin16.png'
    class_icon48 = 'images/Skin48.png'

    __fixed_handlers__ = ['template.xhtml.en']


    def get_breadcrumb(self):
        """Return a list of dicts [{name, url}...] """
        context = get_context()
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
                url = here.get_pathto(handler)
            else:
                url = '%s/;%s' % (here.get_pathto(handler), view)
            # The title
            title = handler.get_title_or_name()
            short_title = reduce_string(title, 15, 30) 
            # Name
            breadcrumb.append({'name': title, 'short_name': short_title,
                               'url': url})

        return breadcrumb


    def get_metadata(self):
        context = get_context()
        request = context.request
        here = context.handler

        namespace = {}

        namespace['title'] = here.get_title_or_name()
        namespace['format'] = here.class_title
        namespace['language'] = here.get_property('dc:language')
        namespace['mtime'] = here.get_mtime().strftime('%Y-%m-%d %H:%M')
        namespace['icon'] = here.get_path_to_icon(size=48)

        # Languages
        site_root = here.get_site_root()
        site_languages = site_root.get_property('ikaaro:website_languages')
        language = context.get_cookie('content_language') or site_languages[0]
        languages = []
        for x in site_languages:
            languages.append({'code': x,
                              'name': i18n.get_language_name(x),
                              'is_selected': x == language})
        namespace['languages'] = languages

        return namespace


    def get_tabs(self):
        """
        Return tabs and subtabs as a dict {tabs, subtabs} of list of dicts
        [{name, label, active, style}...].
        """
        # Get request, path, etc...
        context = get_context()
        here = context.handler

        # Tabs
        views = here.get_views()
        subviews = here.get_subviews(context.method)

        tabs = []
        for name in views:
            method = here.get_method(name)
            if method is not None:
                label = getattr(method.im_class, '%s__label__' % name)
                active = name == context.method or name in subviews
                tabs.append({'name': ';%s' % name,
                             'label': here.gettext(label),
                             'active': active,
                             'style': active and 'tab_active' or 'tab'})

        # Subtabs
        subtabs = []
        for name in subviews:
            method = here.get_method(name)
            if method is not None:
                label = getattr(method.im_class, '%s__sublabel__' % name)
                active = name == context.method
                subtabs.append({'name': ';%s' % name,
                                'label': here.gettext(label),
                                'active': active,
                                'style': active and 'tab_active' or 'tab'})

        return {'tabs':tabs, 'subtabs':subtabs}


##    def get_languages(self):
##        """
##        Compute available languages.
##        Return of list of dicts [{id, title, selected}...]
##        """
##        context = get_context()
##        request = context.request
##        root, handler = context.root, context.handler

##        language_action = '%s/;change_language' % handler.get_pathto(root)

##        accept = request.accept_language
##        available_languages = root.get_available_languages()
##        default_language = root.get_default_language()
##        selected_language = accept.select_language(available_languages) \
##                            or default_language

##        languages = [ {'id': x, 'title': i18n.get_language_name(x),
##                       'selected': x == selected_language}
##                      for x in available_languages ]

##        return {'language_action': language_action, 'languages': languages}


    def get_user_menu(self):
        """Return a dict {user_icon, user, joinisopen}."""
        context = get_context()
        user = context.user
        here = context.handler
        root = context.root

        path_to_root = here.get_pathto(root)
        if user is None:
            joinisopen = root.get_property('ikaaro:website_is_open')
            info = None
        else:
            joinisopen = False
            home = '%s/;%s' % (here.get_pathto(user), user.get_firstview())
            info = {'name': user.name,
                    'title': user.title or user.name,
                    'home': home,
                    'logout': '%s/;logout' % path_to_root}
        return {'info': info,
                'joinisopen': joinisopen,
                'login_url': '%s/;login_form' % path_to_root,
                'join_url': '%s/;join_form' % path_to_root}


    def get_navigation_menu(self):
        """Build the namespace for the navigation menu."""
        context = get_context()
        root = context.root
        here = context.handler
        namespace = {}

        root_menu = {}
        root_menu['title'] = root.get_title_or_name()
        root_menu['icon'] = root.get_path_to_icon(size=16, from_handler=here)
        root_menu['path'] = here.get_pathtoroot()
        root_menu['active'] = (here is root)

        namespace['root'] = root_menu

        menu = []
        for handler in root.get_handlers():
            if handler.name.startswith('.'):
                continue
            elif handler.real_handler is not None:
                continue
            elif not isinstance(handler, Folder):
                continue
            elif handler.get_firstview() is None:
                continue
            item = {}
            item['title'] = handler.get_title_or_name()
            item['icon'] = handler.get_path_to_icon(size=16, from_handler=here)
            item['path'] = here.get_pathto(handler)
            item['active'] = (handler is here)
            menu.append(item)

        # sort lexicographically by title
        menu.sort(key=itemgetter('title'))

        namespace['menu'] = menu

        return namespace


    def get_message(self):
        """Return a message string from de request."""
        request = get_context().request
        form = request.form
        if form.has_key('message'):
            message = form['message']
            return unicode(message, 'utf8')
        else:
            return None


    def get_template_title(self):
        """Return the title to give to the template document."""
        context = get_context()
        root = context.root
        here = context.handler
        if root is here:
            return root.get_title_or_name()
        else:
            mapping = {'root_title': root.get_title_or_name(),
                       'here_title': here.get_title_or_name()}
            return here.gettext("%(root_title)s: %(here_title)s") % mapping


    def build_namespace(self):
        context = get_context()

        namespace = {}

        # Resources
        namespace['styles'] = [ x for x in context.styles ]
        namespace['scripts'] = [ x for x in context.scripts ]

        # User menu
        namespace['user']= self.get_user_menu()

        # Navigation menu
        namespace['navigation'] = self.get_navigation_menu()

        # Languages
##        languages = self.get_languages()
##        namespace['language_action'] = languages['language_action']
##        namespace['languages'] = languages['languages']

        # Breadcrumb
        namespace['breadcrumb'] = self.get_breadcrumb()

        # Metadata
        namespace['metadata'] = self.get_metadata()

        # Tabs
        tabs = self.get_tabs()
        namespace['tabs'] = tabs['tabs']
        namespace['subtabs'] = tabs['subtabs']

        # Message
        namespace['message'] = self.get_message()

        return namespace


    def template(self, content):
        context = get_context()
        # Build the namespace
        namespace = self.build_namespace()

        # Content
        namespace['title'] = self.get_template_title()
        namespace['body'] = content
        namespace['handler'] = context.handler

        # Set the encoding to UTF-8
        context.response.set_header('Content-Type', 'text/html; charset=UTF-8')

        # Transform the tree
        handler = self.get_handler('template.xhtml')
        here = uri.generic.Path(context.handler.get_abspath())
        there = uri.generic.Path(handler.get_abspath())
        handler = XHTML.set_template_prefix(handler, here.get_pathto(there))

        # STL
        s = []
        header = handler.header_to_str()
        # XXX Strip XML declaration, because it makes IE6 fall into quirks
        # mode (see http://hsivonen.iki.fi/doctype/)
        header = header.split('\n', 1)[1]
        s.append(header)
        data = stl(handler, namespace)
        s.append(data)
        return ''.join(s)


Folder.register_handler_class(Skin)


#############################################################################
# The folder "/ui"
#############################################################################

skin_registry = {}
def register_skin(name, skin):
    if isinstance(skin, str):
        resource = get_resource(skin)
        skin = Skin(resource)
    skin_registry[name] = skin


# Register the built-in skins
path = get_abspath(globals(), 'ui')
register_skin('aruni', '%s/aruni' % path)


class UI(Folder):

    def _get_handler(self, segment, resource):
        name = segment.name
        if name in skin_registry:
            return skin_registry[name]
        return Folder._get_handler(self, segment, resource)


    def _get_virtual_handler(self, segment):
        name = segment.name
        if name in skin_registry:
            return skin_registry[name]
        return Folder._get_virtual_handler(self, segment)


path = get_abspath(globals(), 'ui')
resource = get_resource(path)
ui = UI(resource)
