# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA


# Import from itools
from itools.handlers import IO
from itools.xml import XML, namespaces


schema = {
    'title': {'type': IO.Unicode},
    'description': {'type': IO.Unicode},
    'publisher': {'type': IO.Unicode},
    'identifier': {'type': IO.String},
    'created': {'type': IO.Date}
    }


class Element(XML.Element):

    namespace = 'http://purl.org/dc/elements/1.1'


    def set_comment(self, comment):
        raise ValueError


    def set_element(self, element):
        raise ValueError


    def set_text(self, text, encoding='UTF-8'):
        text = text.strip()
        type = schema[self.name]
        if type is IO.Unicode:
            self.value = type.decode(text, encoding)
        else:
            self.value = type.decode(text)



class Namespace(namespaces.AbstractNamespace):

    class_uri = 'http://purl.org/dc/elements/1.1'
    class_prefix = 'dc'


    def get_element_schema(name):
        try:
            return schema[name]
        except KeyError:
            raise XML.XMLError, 'unknown property "%s"' % name

    get_element_schema = staticmethod(get_element_schema)


namespaces.set_namespace(Namespace)
