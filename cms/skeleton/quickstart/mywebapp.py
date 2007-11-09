# -*- coding: UTF-8 -*-
# Copyright (C) 2007 Henry Obein <henry@itaapy.com>
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
from datetime import date

# Import from itools
from itools import get_abspath

# Import from itools.cms
from itools.cms.future import Dressable, OrderAware
from itools.cms.html import XHTMLFile
from itools.cms.registry import register_object_class, register_website
from itools.cms.skins import Skin as iSkin, register_skin
from itools.cms.website import WebSite
from itools.cms.binary import Image
from itools.cms.workflow import WorkflowAware

# Import from itws
from menu import get_menu_namespace, Link
from utils import is_back_office



###########################################################################
# Skin
###########################################################################
class Skin(iSkin):

    class_id = 'mywebapp-skin'


    def build_namespace(self, context):
        namespace = iSkin.build_namespace(self, context)
        namespace['tabs'] = get_menu_namespace(context, depth=2,
                                               show_first_child=False,
                                               link_like=Link)
        namespace['today'] = date.today().strftime('%A, %B %d, %Y')
        return namespace



###########################################################################
# Web Site
###########################################################################
class Home(Dressable):
    class_id = 'mywebapp-home'
    class_title = u'Home'
    __fixed_handlers__ = ['left.xhtml', 'right.xhtml']
    schema = {'left': ('left.xhtml', XHTMLFile),
              'right': ('right.xhtml', XHTMLFile)}
    template = '/ui/webapp/Home_view.xml'

    view__access__ = True


class Section(OrderAware, Dressable, WorkflowAware):
    class_id = 'mywebapp-section'
    class_title = 'Section'
    orderable_classes = (Dressable, Link)
    class_views = (Dressable.class_views +
                   [['state_form']] +
                   [['order_folders_form']])
    schema = {'content': ('index.xhtml', XHTMLFile),
              'image': ('image', Image)}
    template = '/ui/webapp/Section_view.xml'

    order_folders_form__label__ = u'Menu'
    state_form__access__ = 'is_allowed_to_edit'


    def get_document_types(self):
        return Dressable.get_document_types(self) + [Link, Section]



class MyWebApp(OrderAware, WebSite):

    class_id = 'mywebapp'
    class_title = u'My web application'
    class_views = WebSite.class_views + [['order_folders_form']]
    class_skin = 'ui/webapp'

    orderable_classes = (Home, Section, Link)
    __fixed_handlers__ = WebSite.__fixed_handlers__ + ['home']

    browse_content__access__ = 'is_authenticated'
    last_changes__access__ = 'is_authenticated'
    order_folders_form__label__ = u'Menu'


    def new(self, **kw):
        WebSite.new(self, **kw)
        cache = self.cache

        handler = Home()
        cache['home'] = handler
        cache['home.metadata'] = handler.build_metadata(
                **{'dc:title': {'en': u'Home'}})


    def is_allowed_to_view(self, user, object):
        if is_back_office() is True and user is None:
            return False
        elif isinstance(object, Image) and object.name == 'image':
            return True

        return WebSite.is_allowed_to_view(self, user, object)


    def get_document_types(self):
        return WebSite.get_document_types(self) + [Section, Link, Dressable]


    #######################################################################
    # User Interface
    #######################################################################
    def GET(self, context):
        return context.uri.resolve2('../home')



###########################################################################
# Register
###########################################################################

# Objects
register_object_class(Home)
register_object_class(Section)
register_object_class(MyWebApp)

# Skin
path = get_abspath(globals(), 'ui/webapp')
skin = Skin(path)
register_skin('webapp', skin)

# Website
register_website(MyWebApp)
