# -*- coding: UTF-8 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from itools.schemas import DublinCore
from namespaces import AbstractNamespace, set_namespace
from xml import XMLError



class Namespace(AbstractNamespace):

    class_uri = 'http://purl.org/dc/elements/1.1/'
    class_prefix = 'dc'


    @staticmethod
    def get_element_schema(name):
        elements_schema = {
            'creator': {'is_empty': False, 'is_inline': False},
            'date': {'is_empty': False, 'is_inline': False},
            'language': {'is_empty': False, 'is_inline': False}
            }
        
        if name not in elements_schema:
            raise XMLError, 'unknown property "%s"' % name
 
        return elements_schema.get(name)


set_namespace(Namespace)
