# -*- coding: UTF-8 -*-
# Copyright (C) ${YEAR} ${AUTHOR_NAME} <${AUTHOR_EMAIL}>
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
from itools.schemas import Schema, register_schema
#from itools.datatypes import DateTime, ...


class ExampleSchema(Schema):

    class_uri = 'http://xml.ikaaro.org/namespaces/skeleton'
    class_prefix = 'skeleton'

    datatypes = {
        #'expiration_date': DateTime,
    }



register_schema(ExampleSchema)
