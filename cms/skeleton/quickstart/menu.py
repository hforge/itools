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
from itools.cms.base import Handler
from itools.cms.future import OrderAware
from itools.cms.registry import register_object_class
from itools.cms.messages import MSG_CHANGES_SAVED
from itools.cms.file import File
from itools.cms.widgets import Breadcrumb, BooleanRadio



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
        # Use the default form without language
        return Handler.new_instance_form.im_func(cls, context)


    def GET(self, context):
        link = self.get_property('menu:link')
        return context.uri.resolve2(link)


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


    #######################################################################
    # API to be used by menu.py get_menu_namespace method
    #######################################################################
    def get_target_info(self):
        """
        Return a tuple with:
        example1 : '_blank', '../../;contact_form'
        example2 : '_top', '../../python'
        example3 : '_blank', 'http://www.google.com'
        """

        new_window = '_top'
        if self.get_property('menu:new_window') is True:
            new_window = '_blank'

        return new_window, self.get_property('menu:link')



register_object_class(Link)

###########################################################################
# Menu gestion
###########################################################################
def get_target_info(context, handler):
    """
    Return a tuple with:
    - a list made with the target path and if any the target handler
    - the target info '_top' or '_blank' or ...
    """
    new_window = '_top'
    new_window, target = handler.get_target_info()

    if target and target.startswith('http://'):
        return [target], new_window

    target_rpath = Path(target)

    # split relative target path and target method if any
    target_method = None
    endswithparams = target_rpath[-1].params
    if endswithparams:
        target_method = target_rpath.pop()

    # get the real target handler
    site_root = context.handler.get_site_root()
    try:
        h = handler.get_handler(target_rpath)
        if target_method is None:
            target_method = ';%s' % h.get_firstview()
        target_path = site_root.get_pathto(h)
    except LookupError:
        return None, None

    # make a url list with the target handler
    target_url = [seg.name for seg in target_path if seg.name]
    if target_method:
        target_url.append(target_method)

    return target_url, new_window



def get_menu_namespace_level(context, url, menu_root, depth, show_first_child,
                             link_like=None):
    """
    Return a tabs list with the following structure:

    tabs = [{'active': False,
             'class': None,
             'id': u'tab_python',
             'label': u'Python',
             'path': '../python',
             'options': ...}, {...}]

    link_like can be class that implement get_target_info method
    """
    if is_datatype(menu_root, OrderAware) is False:
        return {}

    here, user = context.handler, context.user
    items = []
    tabs = {}

    for name in menu_root.get_ordered_folder_names('ordered'):
        # Get the handlers, check security
        handler = menu_root.get_handler(name)

        ac = handler.get_access_control()
        if ac.is_allowed_to_view(user, handler) is False:
            continue

        # Link special case for target and actual_url
        target = '_top'
        actual_url = here.abspath == handler.abspath
        if link_like and isinstance(handler, link_like):
            target_url, new_window = get_target_info(context, handler)
            if target_url:
                actual_url = url == target_url

        # Subtabs
        subtabs = {}
        if depth > 1:
            subtabs = get_menu_namespace_level(context, url, handler, depth-1,
                                               show_first_child, link_like)

        # set active, in_path
        active, in_path = False, name in url
        if actual_url:
            active, in_path = True, False

        # set css class to 'active', 'in_path' or None
        css = (active and 'active') or (in_path and 'in_path') or None

        # set label and description
        label = handler.get_property('dc:title') or name
        description = handler.get_property('dc:description') or label

        # set path
        path = here.get_pathto(handler)
        if show_first_child and depth > 1:
            if subtabs.get('items', None):
                childs = subtabs['items']
                first_child = childs[0]['path']
                first_child = here.get_handler(first_child)
                path = here.get_pathto(first_child)


        items.append({'id': 'tab_%s' % label.lower().replace(' ', '_'),
                      'path': str(path),
                      'name': name,
                      'label': here.gettext(label),
                      'description': here.gettext(description),
                      'active': active,
                      'class': css,
                      'target': target})

        # add options to the last dict in items
        items[-1]['options'] = subtabs
        tabs['items'] = items
    return tabs


def get_menu_namespace(context, depth=3, show_first_child=False, flat=True,
                       link_like=None):
    """ Return dict with the following structure (for depth=3 lvl{0,1,2})

    {'flat': {'lvl0': [item_dic*],
              'lvl1': [item_dic*],
              'lvl2': [item_dic*]},
     'items': [item_dic*]}

    with

    item_dic =  [{'active': False,
                  'class': None,
                  'id': u'tab_python',
                  'label': u'Python',
                  'path': '../python',
                  'options': item_dic}]
    """

    request = context.request
    request_uri = str(request.request_uri)
    site_root = context.handler.get_site_root()
    method, path = context.method, context.uri.path
    url = [seg.name for seg in path if seg.name]
    if method:
        url += [';%s' % method]
    tabs = get_menu_namespace_level(context, url, site_root, depth,
                                    show_first_child, link_like)

    if flat:
        tabs['flat'] = {}
        items = tabs['flat']['lvl0'] = tabs['items']
        # initialize the levels
        for i in range(1, depth):
            tabs['flat']['lvl%s' % i] = None
        exist_items = True
        lvl = 1
        while (items is not None) and exist_items:
            exist_items = False
            for item in items:
                if item['class'] in ['active', 'in_path']:
                    if item['options']:
                        items = exist_items = item['options'].get('items')
                        if items:
                            tabs['flat']['lvl%s' % lvl] = items
                            lvl += 1
                        break
                    else:
                        items = None
                        break
    return tabs



