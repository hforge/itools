# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2003-2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA


# Import from Python
import unittest
from unittest import TestCase

# Import from itools
from itools.resources import get_resource
from itools.handlers import XML


class SchemaTestCase(TestCase):
    def setUp(self):
        # Load the scheme
        r = get_resource('es.xsd')
        doc = XML.Document(r)
#        print doc.children
        self.schema = doc.children[0]

#        print "!!!!!!!!!!!!!!!! Class !!!!!!!!!!!!!!!!!"
#        print self.schema.types
#        for  x in self.schema.types: 
#           print self.schema.types[x].xsd_content

        # Register the scheme
        XML.registry.set_namespace('http://www.lisa.org/tmx', self.schema)
#        XML.registry.set_namespace('http://www.itools.org/namespaces/simple',
#                                   self.schema)
        print"=========================================="
#        print doc.children[0].elements
#        print doc.children[0].types


    def test_simple(self):
       rr = get_resource('es.xml')
       doc = XML.Document(rr)


if __name__ == '__main__':
    unittest.main()
