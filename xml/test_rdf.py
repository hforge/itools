# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2004 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from RDF import RDF



class RDFTestCase(TestCase):
    def test_parsing(self):
        resource = get_resource('test.rdf')
        handler = RDF(resource)

        subject = u'http://www.example.org/index.html'
        self.assertEqual(handler.graph,
                         {subject: [(u'title', u'The itools reference manual'),
                                    (u'description', u'')]})



if __name__ == '__main__':
    unittest.main()
