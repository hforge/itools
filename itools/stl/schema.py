# -*- coding: UTF-8 -*-
# Copyright (C) 2003-2008 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2006 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2007-2008 Henry Obein <henry.obein@gmail.com>
# Copyright (C) 2007-2008 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from itools.datatypes import String
from itools.xml import register_namespace, ElementSchema, XMLNamespace


stl_uri = 'http://www.hforge.org/xml-namespaces/stl'

stl_attributes = {
    'repeat': String,
    'if': String,
    'omit-tag': String}


class STLElement(ElementSchema):

    attributes = stl_attributes


stl_elements = [
    STLElement(name='block', is_inline=False),
    STLElement(name='inline', is_inline=True)]


stl_namespace = XMLNamespace(
    uri=stl_uri,
    prefix='stl',
    elements=stl_elements,
    attributes=stl_attributes)


# Register
register_namespace(stl_namespace)

