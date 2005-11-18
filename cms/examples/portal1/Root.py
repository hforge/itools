# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004-2005 Luis Belmar-Letelier <luis@itaapy.com>
#               2005 Alexandre Fernandez <alex@itaapy.com>
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

# Import from itools
from itools.xml.stl import stl
from itools.cms.Root import Root as ikaaroRoot


class Root(ikaaroRoot):

    class_id = 'Portal'
    class_title = u'Portal one'
    class_description = u'A portal for learning iKaaro'
    class_version = '20041204'


    def get_views(self):
        views = ikaaroRoot.get_views(self)
        views += ['help', 'view']
        return views


    help__label__ = u'Help'
    help__access__ = True
    def help(self):
        return u"Read the doc in README file."  


    view__label__ = u"View's exemple"
    view__access__ = True
    def view(self):
        # Build the namespace
        namespace = {}
        namespace['hello'] = u"Hello world!"

        library = {'category': 'Good Books'}
        records = [{'name': u'Python Cookbook',
                    'value': u"O'Reilly & Associates"},
                   {'name': u"iKaaro for Dummies",
                    'value': u"Publishers of the Future"}]
        library['books'] = records
        namespace['library'] = library

        # Find the hander for our template
        handler = self.get_handler('ui/portal/Root_view.xml')
        return stl(handler, namespace)

ikaaroRoot.register_handler_class(Root)
