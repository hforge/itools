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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA

# Import from the Standard Library
import warnings

# Import from itools
from itools.datatypes import String
from base import Schema



schemas = {}
prefixes = {}


def set_schema(schema):
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


def get_schema(schema_uri):
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


def get_schema_by_prefix(prefix):
    """
    Returns the schema handler associated to the given prefix. If there
    is none the default schema handler is returned, and a warning message
    is issued.
    """
    if prefix in prefixes:
        schema_uri = prefixes[prefix]
        return get_schema(schema_uri)

    # Use default
    warnings.warn('Unknown schema prefix "%s" (using default)' % prefix)
    return schemas[None]


def get_datatype(schema_uri, name):
    if schema_uri in schemas:
        schema = schemas[schema_uri]
    else:
        # Use default
        warnings.warn('Unknown schema "%s" (using default)' % schema_uri)
        schema = schemas[None]
    return schema.get_datatype(name)


def get_datatype_by_prefix(prefix, name):
    schema = get_schema_by_prefix(prefix)
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


set_schema(DefaultSchema)
