# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2007 Juan David Ibáñez Palomar <jdavid@itaapy.com>
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
import warnings

# Import from itools
from itools.datatypes import String, QName
from base import BaseSchema


##############################################################################
# The schemas registry
##############################################################################

schemas = {}
prefixes = {}


def register_schema(schema, *args):
    """
    Associates a schema handler to a schema uri. It a prefix is
    given it also associates that that prefix to the given schema.
    """
    # Register the URI
    schemas[schema.class_uri] = schema

    # Register the prefix
    prefix = schema.class_prefix
    if prefix is not None:
        if prefix in prefixes:
            warnings.warn('The prefix "%s" is already registered.' % prefix)
        prefixes[prefix] = schema.class_uri

    # Register additional URIs
    for uri in args:
        schemas[uri] = schema


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
class DefaultSchema(BaseSchema):

    class_uri = None
    class_prefix = None


    @staticmethod
    def get_datatype(name):
        return String


register_schema(DefaultSchema)
