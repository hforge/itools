# -*- coding: ISO-8859-1 -*-
# Copyright (C) 2005 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Import from the Standard Library
import warnings

# Import from itools
from itools.datatypes import String, QName
from base import Schema


##############################################################################
# The schemas registry
##############################################################################

schemas = {}
prefixes = {}


def register_schema(schema):
    """
    Associates a schema handler to a schema uri. It a prefix is
    given it also associates that that prefix to the given schema.
    """
    schemas[schema.class_uri] = schema

    prefix = schema.class_prefix
    if prefix is not None:
        if prefix in prefixes:
            warnings.warn('The prefix "%s" is already registered.' % prefix)
        prefixes[prefix] = schema.class_uri


##############################################################################
# API
##############################################################################

def get_schema(name):
    """
    Returns the schema handler associated to the given prefix. If there
    is none the default schema handler is returned, and a warning message
    is issued.
    """
    if name in prefixes:
        schema_uri = prefixes[name]
        return get_schema_by_uri(schema_uri)

    # Use default
    if name is not None:
        warnings.warn('Unknown schema prefix "%s" (using default)' % name)
    return schemas[None]


def get_schema_by_uri(schema_uri):
    """
    Returns the schema handler associated to the given uri. If there
    is none the default schema handler will be returned, and a warning
    message will be issued.
    """
    if schema_uri in schemas:
        return schemas[schema_uri]

    # Use default
    warnings.warn('Unknown schema "%s" (using default)' % schema_uri)
    return schemas[None]


def has_schema(schema_uri):
    """
    Returns true if there is schema handler associated to the given uri.
    """
    return schema_uri in schemas


##############################################################################
# API / DataTypes
def get_datatype(qname):
    if isinstance(qname, str):
        qname = QName.decode(qname)

    schema = get_schema(qname[0])
    return schema.get_datatype(qname[1])


def get_datatype_by_uri(schema_uri, name):
    if schema_uri in schemas:
        schema = schemas[schema_uri]
    else:
        # Use default
        warnings.warn('Unknown schema "%s" (using default)' % schema_uri)
        schema = schemas[None]
    return schema.get_datatype(name)


##############################################################################
# The default schema, used when the prefix is None
##############################################################################
class DefaultSchema(Schema):

    class_uri = None
    class_prefix = None


    @staticmethod
    def get_datatype(name):
        return String


register_schema(DefaultSchema)
