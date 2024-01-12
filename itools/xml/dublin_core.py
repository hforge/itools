# Copyright (C) 2005-2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007 Sylvain Taverne <taverne.sylvain@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from itools.datatypes import Unicode, String, ISODateTime
from .namespaces import XMLNamespace, register_namespace, ElementSchema


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
    ElementSchema(name='creator', context='creator', skip_content=True),
    ElementSchema(name='description'),
    ElementSchema(name='date', skip_content=True),
    ElementSchema(name='format'),
    ElementSchema(name='language', skip_content=True),
    ElementSchema(name='publisher'),
    ElementSchema(name='rights'),
    ElementSchema(name='subject'),
    ElementSchema(name='title', context='title'),
    ElementSchema(name='type'),
    ]


dc_namespace = XMLNamespace(
    uri='http://purl.org/dc/elements/1.1/',
    prefix='dc',
    elements=dc_elements,
    attributes=dc_attributes)


###########################################################################
# Register
###########################################################################
register_namespace(dc_namespace)

