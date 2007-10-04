# -*- coding: UTF-8 -*-
# Copyright (C) ${YEAR} ${AUTHOR_NAME} <${AUTHOR_EMAIL}>
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

# Import from itools
from itools.datatypes import is_datatype
from itools.stl import stl
from itools.uri import Path

# Import from itools.cms
from itools.cms.future import OrderAware
from itools.cms.registry import register_object_class
from itools.cms.messages import *
from itools.cms.file import File
from itools.cms.widgets import Breadcrumb, BooleanRadio
from itools.cms import Folder



###########################################################################
# Link
###########################################################################
class Link(File):

    class_id = 'link'
    class_title = u'Link'
    class_description = u'Link'
    class_version = '20070925'
    class_icon48 = 'menu/images/Link48.png'
    class_icon16 = 'menu/images/Link16.png'
    class_views = [['edit_metadata_form'], ['state_form']]


    @classmethod
    def new_instance_form(cls, context):
        # Hack in order to do not copy Folder method
        return Folder.new_instance_form.im_func(cls, context)


    @classmethod
    def new_instance(cls, container, context):
        # Hack in order to do not copy Folder method
        return Folder.new_instance.im_func(cls, container, context)


    def GET(self, context):
        link = self.get_property('menu:link')
        return context.uri.resolve(link)


    def get_target(self):
        if self.get_property('menu:new_window') is True:
            return '_blank'
        return '_top'


    def get_target_names(self):
        """
        Return the target names
        http://abc.org -> http://abc.org
        ../../a/b/;method -> [a, b]
        ../../a/b/c -> [a, b, c]
        ../;method -> [;method]
        """
        target = self.get_property('menu:link')
        if not target or target.startswith('http://'):
            return target
        targets = target.split('/')
        # If the target is the parent
        if len(targets) == 1 and targets == ['..']:
            return targets
        start = 0
        while targets[start] == '..':
            start += 1
        targets = targets[start:]
        if targets[-1][0] == ';' and len(targets) > 1:
            return targets[:-1]
        return targets


    add_link_form__access__ = 'is_allowed_to_edit'
    def addlink_form(self, context):
        # Build the bc
        if isinstance(self, File):
            start = self.parent
        else:
            start = self
        # Construct namespace
        namespace = {}
        namespace['bc'] = Breadcrumb(filter_type=File, start=start)
        namespace['message'] = context.get_form_value('message')

        prefix = Path(self.abspath).get_pathto('/ui/html/addimage.xml')
        handler = self.get_handler('/ui/menu/addlink.xml')
        return stl(handler, namespace, prefix=prefix)


    def edit_metadata_form(self, context):
        # Build the namespace
        namespace = {}
        # Language
        site_root = self.get_site_root()
        languages = site_root.get_property('ikaaro:website_languages')
        default_language = languages[0]
        language = context.get_cookie('content_language') or default_language
        namespace['language'] = language
        # Title
        namespace['title'] = self.get_property('dc:title', language=language)
        # Description
        namespace['description'] = self.get_property('dc:description',
                                                     language=language)
        namespace['menu:link'] = self.get_property('menu:link')
        new_window = self.get_property('menu:new_window')
        labels = {'yes': u'New window', 'no': u'Current window'}
        namespace['target'] = BooleanRadio.to_html(None, 'menu:new_window',
                                                   new_window, labels)
        # Add a script
        here = context.handler
        script = Path(here.abspath).get_pathto('/ui/menu/javascript.js')
        context.scripts.append(str(script))

        handler = self.get_handler('/ui/menu/Link_edit_metadata.xml')
        return stl(handler, namespace)


    def edit_metadata(self, context):
        link = context.get_form_value('menu:link').strip()
        if not link:
            return context.come_back(u'The link must be entered.')

        title = context.get_form_value('dc:title')
        description = context.get_form_value('dc:description')
        new_window = context.get_form_value('menu:new_window')
        language = context.site_root.get_default_language()

        self.set_property('dc:title', title, language=language)
        self.set_property('dc:description', description, language=language)
        self.set_property('menu:link', link)
        self.set_property('menu:new_window', new_window)
        return context.come_back(MSG_CHANGES_SAVED)



register_object_class(Link)


###########################################################################
# Menu gestion
###########################################################################
def get_menu_namespace_level(context, url, parent, depth, show_first_child,
                             flat):
    if is_datatype(parent, OrderAware) is False:
        return {}

    here = context.handler
    last_url = (len(url) == 1)
    tabs = {}
    items = []
    flat_items = []
    user = context.user
    handler_names = parent.get_ordered_folder_names('ordered')
    next_depth = depth - 1
    url = url or ''
    if is_datatype(url, list) is False:
        url = [url]

    for name in handler_names:
        # Get the handlers, check security
        handler = parent.get_handler(name)
        ac = handler.get_access_control()
        if ac.is_allowed_to_view(user, handler) is False:
            continue

        # Subtabs
        subtabs = {}
        if next_depth >= 0:
            subtabs = get_menu_namespace_level(context, url[1:], handler,
                                               next_depth, show_first_child,
                                               flat)

        # Add the menu
        active = False
        in_path = False
        target = '_top'
        # Link
        if isinstance(handler, Link):
            name = handler.get_target_names()
            active = (name == url)
            target = handler.get_target()
        else:
            if name == url[0]:
                if last_url is True: # last level
                    active = True
                else:
                    in_path = True

        label = handler.get_property('dc:title') or name
        if show_first_child and depth >= 1:
            if subtabs.has_key('items') and len(subtabs['items']) > 0:
                path = subtabs['items'][0]['name']
            else:
                path = here.get_pathto(handler)
        else:
            path = here.get_pathto(handler)

        css = (active and 'active') or (in_path and 'in_path') or None
        items.append({'id': 'tab_%s' % label.lower().replace(' ', '_'),
                      'name': path,
                      'label': here.gettext(label),
                      'active': active,
                      'class': css,
                      'target': target})

        if flat and not flat_items and (css in ['in_path', 'active']):
            flat_items = subtabs

        items[-1]['options'] = subtabs
    tabs['items'] = items
    if flat:
        tabs['flat_items'] = flat_items
    return tabs


def get_menu_namespace(context, depth=3, show_first_child=False, flat=True):
    """
    Return tabs and subtabs as a dict {tabs, subtabs} of list of dicts
    [{name, label, active, style}...].
    """
    # Get request, path, etc...
    request = context.request
    user = context.user
    here = context.handler
    site_root = here.get_site_root()
    if here is None:
        return []

    request_uri = str(request.request_uri)
    if request_uri[0] == '/':
        request_uri = request_uri[1:]

    # split the url
    url = request_uri.split(';')
    if url[0] == '' and len(url) == 2:
        url = ';%s' % url[1]
    else:
        url = url[0]
    if url and url[-1] == '/':
        url = url[:-1]
    url = url.split('/')
    tabs = get_menu_namespace_level(context, url, site_root, depth,
                                    show_first_child, flat)

    return tabs



