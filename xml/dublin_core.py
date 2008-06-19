# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
from namespaces import AbstractNamespace, set_namespace
from parser import XMLError


class Namespace(AbstractNamespace):

    class_uri = 'http://purl.org/dc/elements/1.1/'
    class_prefix = 'dc'

    datatypes = {'contributor': None,
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
                 'type': None,
                 }

    elements_schema = {
        'creator': {'is_empty': False, 'is_inline': False},
        'description': {'is_empty': False, 'is_inline': False},
        'date': {'is_empty': False, 'is_inline': False,
                 'translate_content': False},
        'language': {'is_empty': False, 'is_inline': False,
                          'translate_content': False},
        'subject': {'is_empty': False, 'is_inline': False},
        'title': {'is_empty': False, 'is_inline': False}
        }

