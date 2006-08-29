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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from itools
from itools.datatypes import Unicode
from itools.xml import XML, namespaces
from itools.schemas.dublin_core import DublinCore



class Element(XML.Element):

    namespace = 'http://purl.org/dc/elements/1.1'


    def set_comment(self, comment):
        raise ValueError


    def set_element(self, element):
        raise ValueError


    def set_text(self, text, encoding='UTF-8'):
        text = text.strip()
        type = DublinCore.datatypes[self.name]
        if type is Unicode:
            self.value = type.decode(text, encoding)
        else:
            self.value = type.decode(text)



class Namespace(namespaces.AbstractNamespace):

    class_uri = 'http://purl.org/dc/elements/1.1'
    class_prefix = 'dc'


    @staticmethod
    def get_element_schema(name):
        if name not in schema:
            raise XML.XMLError, 'unknown property "%s"' % name

        return Element


namespaces.set_namespace(Namespace)
