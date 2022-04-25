# -*- coding: UTF-8 -*-
# Copyright (C) 2005-2008, 2010 J. David Ibáñez <jdavid.ibp@gmail.com>
# Copyright (C) 2008 David Versmisse <versmisse@lil.univ-littoral.fr>
# Copyright (C) 2008 Sylvain Taverne <taverne.sylvain@gmail.com>
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
from warnings import warn

# Import from itools
from itools.core import proto_lazy_property, prototype
from itools.datatypes import String
from .parser import XMLError


"""
This module keeps a registry for namespaces and namespace handlers.

Namespace handlers are used through the parsing process, they are
responsible to deal with the elements and attributes associated to
them.

This module provides an API to register namespace uris and handlers,
and to ask this registry.
"""



xml_uri = 'http://www.w3.org/XML/1998/namespace'
xmlns_uri = 'http://www.w3.org/2000/xmlns/'


###########################################################################
# The registry
###########################################################################
namespaces = {}


def register_namespace(namespace, *args):
    """Associates a namespace handler to a namespace uri.
    """
    # Register the URI
    namespaces[namespace.uri] = namespace

    # Register additional URIs
    for uri in args:
        namespaces[uri] = namespace


def get_namespace(namespace_uri):
    """Returns the namespace handler associated to the given uri. If there
    is none the default namespace handler will be returned, and a warning
    message will be issued.
    """
    if namespace_uri in namespaces:
        return namespaces[namespace_uri]

    # Use default
    warn('Unknown namespace "%s" (using default)' % namespace_uri)
    return namespaces[None]


def has_namespace(namespace_uri):
    """Returns true if there is namespace handler associated to the given uri.
    """
    return namespace_uri in namespaces


###########################################################################
# API
###########################################################################

def get_element_schema(namespace, name):
    return get_namespace(namespace).get_element_schema(name)


def is_empty(namespace, name):
    schema = get_namespace(namespace).get_element_schema(name)
    return getattr(schema, 'is_empty', False)


def get_attr_datatype(tag_uri, tag_name, attr_uri, attr_name,
                      attributes=None):
    # Namespace declaration
    if (attr_uri == xmlns_uri) or (attr_uri is None and attr_name == 'xmlns'):
        return String

    # Attached attribute
    if attr_uri is None or attr_uri == tag_uri:
        element_schema = get_element_schema(tag_uri, tag_name)
        datatype = element_schema.get_attr_datatype(attr_name, attributes)
    else:
        # Free attribute
        datatype = get_namespace(attr_uri).get_attr_datatype(attr_name)
    # No datatype
    if datatype is None:
        message = 'unexpected "%s" attribute for "%s" element'
        raise XMLError(message % (attr_name, tag_name))
    # Ok
    return datatype



###########################################################################
# Namespaces
###########################################################################

class ElementSchema(prototype):

    # Default values
    name = None
    attributes = {}
    is_empty = False
    is_inline = False

    # i18n default values
    default_datatype = None
    skip_content = False
    keep_spaces = False
    context = None

    def get_attr_datatype(self, name, attributes):
        datatype = self.attributes.get(name)
        if datatype is not None:
            return datatype
        if self.default_datatype is not None:
            return self.default_datatype
        return None




class XMLNamespace(prototype):

    uri = None
    prefix = None
    elements = []
    free_attributes = {}
    default_datatype = String
    default_element = None


    @proto_lazy_property
    def elements_kw(self):
        kw = {}
        for element in self.elements:
            name = element.name
            if name in self.elements:
                raise ValueError('element "%s" is defined twice' % name)
            kw[name] = element
        return kw


    def get_element_schema(self, name):
        """Returns a dictionary that defines the schema for the given element.
        """
        element = self.elements_kw.get(name)
        if element is not None:
            return element
        if self.default_element is not None:
            return self.default_element(name=name)
        raise XMLError('unexpected element "%s"' % name)


    def get_attr_datatype(self, name):
        datatype = self.free_attributes.get(name)
        if datatype is not None:
            return datatype
        if self.default_datatype is not None:
            return self.default_datatype
        return None



# The default namespace is used for free elements.
default_namespace = XMLNamespace(uri=None, prefix=None, default_element=ElementSchema)



# The builtin "xml:" namespace
xml_namespace = XMLNamespace(
    xml_uri, 'xml',
    free_attributes={
        'lang': String,
        'space': String,
        'base': String,
        'id': String})


# The builtin "xmlns:" namespace, for namespace declarations
class XMLNSNamespace(XMLNamespace):

    def get_attr_datatype(self, name):
        return String


xmlns_namespace = XMLNSNamespace(uri=xmlns_uri, prefix='xmlns')


###########################################################################
# Register
###########################################################################
register_namespace(xml_namespace)
register_namespace(xmlns_namespace)
register_namespace(default_namespace)
