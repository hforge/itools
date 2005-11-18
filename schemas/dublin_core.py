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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA

# Import from itools
from itools.datatypes.primitive import Unicode, String, DateTime
from base import Schema
import registry



class DublinCore(Schema):

    class_uri = 'http://purl.org/dc/elements/1.1'
    class_prefix = 'dc'


    datatypes = {'contributor': None,
                 'coverage': None,
                 'creator': None,
                 'date': DateTime,
                 'description': Unicode,
                 'format': None,
                 'identifier': String,
                 'language': String,
                 'publisher': Unicode,
                 'relation': None,
                 'rights': None,
                 'source': None,
                 'subject': None,
                 'title': Unicode,
                 'type': None,
                 }


registry.register_schema(DublinCore)
