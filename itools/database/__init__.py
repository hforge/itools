# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008, 2010-2011 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2007, 2011 Hervé Cauwelier <herve@oursours.net>
# Copyright (C) 2010-2011 David Versmisse <versmisse@lil.univ-littoral.fr>
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
from fields import Field, get_field_and_datatype
from queries import AllQuery, NotQuery, StartQuery, TextQuery
from queries import RangeQuery, PhraseQuery, AndQuery, OrQuery, pprint_query
from magic_ import magic_from_buffer, magic_from_file
from metadata import Metadata
from metadata_parser import MetadataProperty
from registry import get_register_fields, register_field
from resources import Resource
from ro import RODatabase, ReadonlyError
from rw import RWDatabase, make_database


__all__ = [
    'magic_from_buffer',
    'magic_from_file',
    # Database
    'ReadonlyError',
    'RODatabase',
    'RWDatabase',
    'make_database',
    'get_register_fields',
    'register_field',
    # Metadata
    'Metadata',
    'MetadataProperty',
    # Resources
    'Field',
    'get_field_and_datatype',
    'Resource',
    # Queries
    'RangeQuery',
    'PhraseQuery',
    'AndQuery',
    'OrQuery',
    'AllQuery',
    'NotQuery',
    'StartQuery',
    'TextQuery',
    'pprint_query']
