# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008 Juan David Ibáñez Palomar <jdavid@itaapy.com>
# Copyright (C) 2007 Sylvain Taverne <sylvain@itaapy.com>
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
from datetime import datetime

# Import from itools
from itools.datatypes import Unicode, String, ISODateTime
from namespaces import XMLNamespace, register_namespace, ElementSchema
from parser import XMLError


dc_attributes = {
    'contributor': None,
    'coverage': None,
    'creator': String,
    'date': ISODateTime,
    'description': Unicode,
    'format': None,
    'identifier': String,
    'language': String,
    'publisher': Unicode,
    'relation': None,
    'rights': None,
    'source': None,
    'subject': Unicode,
    'title': Unicode,
    'type': None}


dc_elements = [
    ElementSchema('creator', context='creator'),
    ElementSchema('description'),
    ElementSchema('date', skip_content=True),
    ElementSchema('language', skip_content=True),
    ElementSchema('subject'),
    ElementSchema('title', context='title'),
    ]


dc_namespace = XMLNamespace(
    'http://purl.org/dc/elements/1.1/', 'dc',
    dc_elements,
    dc_attributes)



###########################################################################
# Register
###########################################################################
register_namespace(dc_namespace)

